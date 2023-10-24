from typing import Union

from sqlalchemy.ext.asyncio import create_async_engine as create_engine
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine


def create_async_engine(url: Union[URL, str]) -> AsyncEngine:
    return create_engine(url=url, echo=True)


async def proceed_schemas(engine: AsyncEngine, metadata) -> None:
    async with engine.connect() as conn:
        await conn.run_sync(metadata.create_all)
        await conn.commit()
