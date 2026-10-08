from app.realtime.dispatcher import Dispatcher
from app.realtime.handlers import (
    message_handler,
    receipt_handler,
    sync_handler,
    system_handler,
    typing_handler,
)


def build_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    for module in (message_handler, receipt_handler, typing_handler, sync_handler, system_handler):
        dispatcher.register_all(module.HANDLERS)
    return dispatcher
