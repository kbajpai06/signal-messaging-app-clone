from app.core.errors import AppError, PayloadTooLargeError, UnsupportedMediaError
from app.services.storage import FileStorage
from app.utils.ids import new_id
from app.utils.images import detect_image_type

AVATAR_FOLDER = "avatars"


class AvatarService:
    def __init__(self, storage: FileStorage, *, max_bytes: int) -> None:
        self._storage = storage
        self._max_bytes = max_bytes

    async def store(self, data: bytes) -> str:
        if not data:
            raise AppError("The uploaded file is empty", code="empty_file")
        if len(data) > self._max_bytes:
            raise PayloadTooLargeError(
                f"Image must be smaller than {self._max_bytes // 1024} KB", code="file_too_large"
            )
        kind = detect_image_type(data)
        if kind is None:
            raise UnsupportedMediaError(
                "Avatar must be a PNG, JPEG, GIF or WebP image", code="unsupported_image"
            )
        return await self._storage.save(
            folder=AVATAR_FOLDER, filename=f"{new_id()}.{kind}", data=data
        )

    async def discard(self, url: str | None) -> None:
        if url:
            await self._storage.delete(url)
