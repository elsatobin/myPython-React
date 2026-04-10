import mimetypes
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import STORAGE_DIR
from src.files.models import StoredFile
from src.files.repository import FileRepository


class FileService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = FileRepository(session)

    async def list_files(self) -> list[StoredFile]:
        return await self.repo.get_all()

    async def get_file(self, file_id: str) -> StoredFile:
        file = await self.repo.get_by_id(file_id)
        if not file:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        return file

    async def create_file(self, title: str, upload_file: UploadFile) -> StoredFile:
        content = await upload_file.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")

        file_id = str(uuid4())
        suffix = Path(upload_file.filename or "").suffix
        stored_name = f"{file_id}{suffix}"
        (STORAGE_DIR / stored_name).write_bytes(content)

        file = StoredFile(
            id=file_id,
            title=title,
            original_name=upload_file.filename or stored_name,
            stored_name=stored_name,
            mime_type=(
                upload_file.content_type
                or mimetypes.guess_type(stored_name)[0]
                or "application/octet-stream"
            ),
            size=len(content),
            processing_status="uploaded",
        )
        return await self.repo.save(file)

    async def update_file(self, file_id: str, title: str) -> StoredFile:
        file = await self.get_file(file_id)
        return await self.repo.update_fields(file, title=title)

    async def delete_file(self, file_id: str) -> None:
        file = await self.get_file(file_id)
        stored_path = STORAGE_DIR / file.stored_name
        if stored_path.exists():
            stored_path.unlink()
        await self.repo.delete(file)

    async def get_file_path(self, file_id: str) -> tuple[StoredFile, Path]:
        file = await self.get_file(file_id)
        stored_path = STORAGE_DIR / file.stored_name
        if not stored_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found"
            )
        return file, stored_path
