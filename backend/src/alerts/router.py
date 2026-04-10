from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.alerts.repository import AlertRepository
from src.alerts.schemas import AlertItem
from src.core.database import async_session_maker

router = APIRouter(prefix="/alerts", tags=["alerts"])


async def get_session() -> AsyncSession:  # type: ignore[return]
    async with async_session_maker() as session:
        yield session


@router.get("", response_model=list[AlertItem])
async def list_alerts(session: AsyncSession = Depends(get_session)):
    return await AlertRepository(session).get_all()
