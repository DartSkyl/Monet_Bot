from database.base import BotBase
from config_data.config import BOT_TOKEN, DB_INFO, MAIN_GROUP_ID
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage


db = BotBase(DB_INFO[0], DB_INFO[1], DB_INFO[2], DB_INFO[3])

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())
admins_id = list()


async def db_connect():
    await db.connect()
    await db.check_db_structure()


async def admin_list_load():
    admins = await bot.get_chat_administrators(chat_id=MAIN_GROUP_ID)
    admins = {admin.user.id for admin in admins}
    for admin_id in admins:
        admins_id.append(admin_id)
