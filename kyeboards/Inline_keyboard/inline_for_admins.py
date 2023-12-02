from loader import subscription_dict, channels_dict, bot, db
from aiogram import html
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData


class SubAddForChannel(CallbackData, prefix='sub'):
    """Класс коллбэков для добавления варианта подписки на канал"""
    chn_id: str
    chn_name: str


class SubDel(CallbackData, prefix='subdel'):
    """Класс коллбэков для удаления вариантов подписки"""
    sub_period: int
    chnl_id: int


class AddSubForUser(CallbackData, prefix='addsub'):
    """Класс коллбэков для добавления подписки пользователю вручную"""
    chl_id: int
    chl_name: str


def del_board(chl_list):
    """Функция возвращает inline клавиатуру для удаления подписок"""
    sub_del_board = InlineKeyboardBuilder()
    paid_channels = chl_list
    for chann in paid_channels:
        sub_del_board.button(text=str(chann['channel_name'] + ':'), callback_data='0')
        for period, cost in sorted(subscription_dict[chann['channel_id']].items()):
            if period != 0:
                button_text = f'Удалить подписку на {period} дня/дней стоимостью {cost} рублей'
                sub_del_board.button(text=button_text,
                                     callback_data=SubDel(sub_period=period, chnl_id=int(chann["channel_id"])))
        # Если в словаре хранится только пробный период или нет даже его (хотя такого быть не должно)
        if len(subscription_dict[chann['channel_id']]) <= 1:
            button_text = 'Нет вариантов платной подписки для этого канала!'
            sub_del_board.button(text=button_text, callback_data='00')
    sub_del_board.adjust(1)
    return sub_del_board.as_markup(resize_keyboard=True)


async def add_sub_channel_keyboard():
    """Функция возвращает клавиатуру с каналами для добавления варианта подписки. И для пробной тоже"""
    sub_channel_keyboard = InlineKeyboardBuilder()
    paid_channels = await db.get_paid_channels_list()
    for channel in paid_channels:
        sub_channel_keyboard.button(text=channel['channel_name'],
                                    callback_data=SubAddForChannel(chn_id=str(channel['channel_id']),
                                                                   chn_name=str(channel['channel_name'])))
    sub_channel_keyboard.adjust(1)
    return sub_channel_keyboard.as_markup(resize_keyboard=True)


async def add_sub_keyboard():
    """Функция возвращает клавиатуру для добавления подписки пользователю в ручную.
    Клавиатура со списком доступных каналов для добавления подписки (т.е. закрытых, channels_dict['is_paid'])"""
    add_sub_board = InlineKeyboardBuilder()
    for ch_id in channels_dict['is_paid']:
        chl_info = await bot.get_chat(chat_id=ch_id)
        add_sub_board.button(text=str(chl_info.title),
                             callback_data=AddSubForUser(chl_id=ch_id, chl_name=chl_info.title))
    add_sub_board.adjust(1)
    return add_sub_board.as_markup(resize_keyboard=True)
