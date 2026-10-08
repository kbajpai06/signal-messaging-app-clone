import asyncio
from pathlib import Path
from typing import Protocol


class FileStorage(Protocol):
    async def save(self, *, folder: str, filename: str, data: bytes) -> str:
        """Persist bytes and return the public URL path."""
        ...

    async def delete(self, public_path: str) -> None: ...


class LocalFileStorage:
    def __init__(self, root: Path, url_prefix: str = "/uploads") -> None:
        self._root = root.resolve()
        self._prefix = url_prefix.rstrip("/")

    async def save(self, *, folder: str, filename: str, data: bytes) -> str:
        target = self._root / folder / filename
        await asyncio.to_thread(self._write, target, data)
        return f"{self._prefix}/{folder}/{filename}"

    async def delete(self, public_path: str) -> None:
        if not public_path.startswith(f"{self._prefix}/"):
            return
        relative = public_path[len(self._prefix) + 1 :]
        target = (self._root / relative).resolve()
        if not target.is_relative_to(self._root):
            return
        await asyncio.to_thread(target.unlink, missing_ok=True)

    @staticmethod
    def _write(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
