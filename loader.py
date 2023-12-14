from typing import List, Dict

from database.base import BotBase
from config_data.config import BOT_TOKEN, DB_INFO, MAIN_GROUP_ID

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# from apscheduler.schedulers.asyncio import AsyncIOScheduler


db = BotBase(DB_INFO[0], DB_INFO[1], DB_INFO[2], DB_INFO[3])

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot=bot, storage=MemoryStorage())

# В этом списке будем хранить ID всех администраторов
admins_id: List[int] = list()

# В этом словаре будут храниться группы. Данный словарь будет использоваться
# для апдэйтов chat_member и не только,
# как оперативная память, что бы каждый раз не обращаться к БД.
# Словарь содержит два ключа: один для открытых каналов, один для платных.
# Значением каждого ключа является список с ID соответствующих каналов
channels_dict = {
    "free": [],
    "is_paid": []
}

# Переписать!!!!!!!!!!!!!!!!!!!!!!!!!

# В этом словаре хранятся варианты для платной подписки.
# Ключ это срок подписки в сутках, а значение это стоимость.
# Например:{'30': 100} - это подписка на 30 суток стоимостью 100 рублей
# За исключением ключа "0". Под этим ключом хранится период пробной подписки в секундах
subscription_dict = dict()


async def db_connect():
    """В этой функции идет подключение к БД и проверка ее структуры"""
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


async def sub_settings_load():
    """Функция загружает из БД настройки для подписок в оперативную память"""

    # Прописать ситуация для первого запуска, когда нет даже ключа 0 для пробной подписки!!!!!!!!!!!!!!!!!!!!!!!!!!!

    # Так же вариант действий для удаления группы из бота

    st_list = await db.get_sub_setting()
    for elem in st_list:
        dict_content = elem['chl_id_period'].split('_')
        if int(dict_content[0]) in subscription_dict:
            subscription_dict[int(dict_content[0])][int(dict_content[1])] = elem['cost']
        else:
            subscription_dict[int(dict_content[0])] = {int(dict_content[1]): elem['cost']}
