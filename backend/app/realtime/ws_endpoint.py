import asyncio
import logging

from fastapi import APIRouter, WebSocket
from pydantic import ValidationError
from starlette.websockets import WebSocketDisconnect

from app.core.errors import AppError, UnauthorizedError
from app.realtime import lifecycle
from app.realtime.connection import Connection, safe_close, safe_send
from app.realtime.context import ConnectionContext, RealtimeRuntime
from app.realtime.handlers import build_dispatcher
from app.realtime.origin import is_origin_allowed
from app.realtime.protocol import (
    CLOSE_FORBIDDEN,
    CLOSE_IDLE,
    CLOSE_UNAUTHENTICATED,
    CLOSE_UNSUPPORTED,
    ProtocolError,
    error_frame,
    parse_client_frame,
    server_frame,
)
from app.schemas.ws_events import AuthPayload
from app.services.auth_service import AuthContext
from app.services.factory import build_auth_service
from app.utils.time import now_ms

logger = logging.getLogger(__name__)

router = APIRouter()
dispatcher = build_dispatcher()

HANDSHAKE_TIMEOUT_S = 5
IDLE_TIMEOUT_S = 75  # clients ping every ~25s


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    runtime: RealtimeRuntime = websocket.app.state.realtime
    # Accept first: custom close codes (4401/4403) are only delivered after the upgrade.
    await websocket.accept()

    if not is_origin_allowed(websocket.headers.get("origin"), runtime.settings):
        await safe_close(websocket, CLOSE_FORBIDDEN, "origin not allowed")
        return

    handshake = await _handshake(websocket, runtime)
    if handshake is None:
        return
    auth, request_id = handshake

    connection = Connection(websocket, user_id=auth.user.id, session_id=auth.session_id)
    ctx = ConnectionContext(
        user=auth.user, connection=connection, expires_at=auth.expires_at, runtime=runtime
    )
    await _serve(ctx, request_id)


async def _receive_text(websocket: WebSocket) -> str:
    message = await websocket.receive()
    if message["type"] == "websocket.disconnect":
        raise WebSocketDisconnect(message.get("code", 1000))
    text = message.get("text")
    if text is None:
        raise ProtocolError(
            "unsupported_frame", "Binary frames are not supported", close_code=CLOSE_UNSUPPORTED
        )
    return text


async def _handshake(
    websocket: WebSocket, runtime: RealtimeRuntime
) -> tuple[AuthContext, str | None] | None:
    """The first frame must be {type: "auth", payload: {token}} within 5s."""
    request_id: str | None = None
    try:
        text = await asyncio.wait_for(_receive_text(websocket), HANDSHAKE_TIMEOUT_S)
        envelope = parse_client_frame(text)
        request_id = envelope.id
        if envelope.type != "auth":
            raise UnauthorizedError("The first frame must be an auth event", code="auth_required")
        token = AuthPayload.model_validate(envelope.payload).token
        async with runtime.session_factory() as db:
            auth = await build_auth_service(db, runtime.settings).authenticate(token)
        return auth, request_id
    except TimeoutError:
        await safe_close(websocket, CLOSE_UNAUTHENTICATED, "auth timeout")
    except WebSocketDisconnect:
        pass
    except ProtocolError as exc:
        await _reject(websocket, request_id, exc.code, exc.message)
    except ValidationError:
        await _reject(websocket, request_id, "invalid_auth", "A token is required")
    except AppError as exc:
        await _reject(websocket, request_id, exc.code, exc.message)
    return None


async def _reject(websocket: WebSocket, request_id: str | None, code: str, message: str) -> None:
    await safe_send(websocket, error_frame(request_id, code, message))
    await safe_close(websocket, CLOSE_UNAUTHENTICATED, code)


async def _serve(ctx: ConnectionContext, request_id: str | None) -> None:
    runtime, connection, user = ctx.runtime, ctx.connection, ctx.user

    peers = await lifecycle.load_peers(runtime, user.id)
    online_ids = [uid for uid in peers if runtime.manager.is_online(uid)]
    sent = await connection.send(
        server_frame(
            "auth.ok",
            {"user_id": user.id, "server_time": now_ms(), "online_user_ids": online_ids},
            reply_to=request_id,
        )
    )
    if not sent:
        return

    # auth.ok goes out BEFORE registration, so it is always the first frame the client sees.
    # The client's follow-up `sync` is processed after registration, so no message is missed.
    first = runtime.manager.register(connection)
    try:
        await lifecycle.on_connected(runtime, user, peers, first=first)
        await _receive_loop(ctx)
    except WebSocketDisconnect:
        pass
    finally:
        last = runtime.manager.unregister(connection)
        await connection.close(1000)
        await lifecycle.on_disconnected(runtime, user.id, last=last)


async def _receive_loop(ctx: ConnectionContext) -> None:
    connection = ctx.connection
    while not connection.closed:
        try:
            text = await asyncio.wait_for(_receive_text(connection.websocket), IDLE_TIMEOUT_S)
            envelope = parse_client_frame(text)
        except TimeoutError:
            await connection.close(CLOSE_IDLE, "idle timeout")
            return
        except ProtocolError as exc:
            if exc.close_code is not None:
                await connection.close(exc.close_code, exc.code)
                return
            await connection.send(error_frame(None, exc.code, exc.message))
            continue

        if now_ms() >= ctx.expires_at:
            await connection.close(CLOSE_UNAUTHENTICATED, "session expired")
            return
        # Handled inline so events from one socket keep their order (typing before send, etc.).
        await dispatcher.dispatch(ctx, envelope)
