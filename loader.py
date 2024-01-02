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

# Словарь будет заполнен значениями "по-умолчанию",
# а при перезапуске бота, если в БД будут другие значения, то просто заменим
users_mess_dict = {
    'hi_mess': 'Добро пожаловать! 😉',
    'trail_sub': 'Вам выдана пробная подписка',
    'not_trail': 'Что бы получить доступ к контенту, нужно оплатить подписку',
    'was_trail': 'Пробная подписка на этот канал Вам уже выдавалась!',
    'sub_end': 'Ваша подписка закончится через сутки',
    'sub_stop': 'Ваша подписка закончилась',
}


async def db_connect():
    """В этой функции идет подключение к БД и проверка ее структуры"""
    await db.connect()
    await db.check_db_structure()


async def load_user_messages():
    """Функция выгружает пользовательские сообщения в оперативную память"""
    messages = await db.get_users_messages()

    for mess in messages:
        users_mess_dict[mess['mess_for']] = mess['mess_text']


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
    st_list = await db.get_sub_setting()
    for elem in st_list:
        dict_content = elem['chl_id_period'].split('_')
        if int(dict_content[0]) in subscription_dict:
            subscription_dict[int(dict_content[0])][int(dict_content[1])] = elem['cost']
        else:
            subscription_dict[int(dict_content[0])] = {int(dict_content[1]): elem['cost']}
