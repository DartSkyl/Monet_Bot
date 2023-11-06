from database.base import BotBase
from config_data.config import BOT_TOKEN, DB_INFO, MAIN_GROUP_ID
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage


db = BotBase(DB_INFO[0], DB_INFO[1], DB_INFO[2], DB_INFO[3])

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())

# В этом списке будем хранить ID всех администраторов
admins_id = list()

# В этом словаре будут храниться группы. Данный словарь будет использоваться для апдэйтов chat_member,
# как оперативная память, что бы каждый раз не обращаться к БД.
# Словарь содержит два ключа: один для открытых каналов, один для платных.
# Значением каждого ключа является список с ID соответствующих каналов
channels_dict = {
    "free": [],
    "is_paid": []
}


async def db_connect():
    await db.connect()
    await db.check_db_structure()


async def admin_list_load():
    """Функция заносит в список ID администраторов из основной группы при включении бота."""
    admins = await bot.get_chat_administrators(chat_id=MAIN_GROUP_ID)
    admins = {admin.user.id for admin in admins}
    for admin_id in admins:
        admins_id.append(admin_id)


async def channels_load():
    """Функция подгружает из базы уже имеющиеся каналы.
    При первом включении, с пустой базой, она ничего не загрузит"""
    chn_lst = await db.get_channel_list()
    for chn in chn_lst:
        if chn['is_paid']:
            channels_dict['is_paid'].append(chn['channel_id'])
        else:
            channels_dict['free'].append(chn['channel_id'])
