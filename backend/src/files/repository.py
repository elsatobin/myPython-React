from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.files.models import StoredFile


class FileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self) -> list[StoredFile]:
        result = await self.session.execute(
            select(StoredFile).order_by(StoredFile.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, file_id: str) -> StoredFile | None:
        return await self.session.get(StoredFile, file_id)

    async def save(self, file: StoredFile) -> StoredFile:
        self.session.add(file)
        await self.session.commit()
        await self.session.refresh(file)
        return file

    async def delete(self, file: StoredFile) -> None:
        await self.session.delete(file)
        await self.session.commit()

    async def update_fields(self, file: StoredFile, **fields) -> StoredFile:
        for key, value in fields.items():
            setattr(file, key, value)
        file.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(file)
        return file
