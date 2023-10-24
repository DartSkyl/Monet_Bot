from config_data.config import DB_INFO
from loader import dp
import handlers  # noqa
from database import  MainBotModel, create_async_engine, proceed_schemas
from sqlalchemy.engine import URL
from aiogram import executor


async def start_up(_):
    postgre_url = URL.create(
        drivername="postgresql+asyncpg",
        username=DB_INFO[0],
        password=DB_INFO[1],
        database=DB_INFO[2],
        port=DB_INFO[3],
        host="localhost",
    )
    async_engine = create_async_engine(postgre_url)
    await proceed_schemas(async_engine, MainBotModel.metadata)

if __name__ == '__main__':
    executor.start_polling(dispatcher=dp, on_startup=start_up)
