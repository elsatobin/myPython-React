from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.core.database import async_session_maker
from src.files.schemas import FileItem, FileUpdate
from src.files.service import FileService
from src.worker.tasks import scan_file_for_threats

router = APIRouter(prefix="/files", tags=["files"])


async def get_session() -> AsyncSession:  # type: ignore[return]
    async with async_session_maker() as session:
        yield session


def get_service(session: AsyncSession = Depends(get_session)) -> FileService:
    return FileService(session)


@router.get("", response_model=list[FileItem])
async def list_files(service: FileService = Depends(get_service)):
    return await service.list_files()


@router.post("", response_model=FileItem, status_code=status.HTTP_201_CREATED)
async def create_file(
    title: str = Form(...),
    file: UploadFile = File(...),
    service: FileService = Depends(get_service),
):
    file_item = await service.create_file(title=title, upload_file=file)
    scan_file_for_threats.delay(file_item.id)
    return file_item


@router.get("/{file_id}", response_model=FileItem)
async def get_file(file_id: str, service: FileService = Depends(get_service)):
    return await service.get_file(file_id)


@router.patch("/{file_id}", response_model=FileItem)
async def update_file(
    file_id: str,
    payload: FileUpdate,
    service: FileService = Depends(get_service),
):
    return await service.update_file(file_id=file_id, title=payload.title)


@router.get("/{file_id}/download")
async def download_file(file_id: str, service: FileService = Depends(get_service)):
    file_item, stored_path = await service.get_file_path(file_id)
    return FileResponse(
        path=stored_path,
        media_type=file_item.mime_type,
        filename=file_item.original_name,
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: str, service: FileService = Depends(get_service)):
    await service.delete_file(file_id)
