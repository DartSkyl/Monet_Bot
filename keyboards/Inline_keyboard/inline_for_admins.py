from loader import subscription_dict, channels_dict, bot, db
from aiogram import html
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData


# ========== Классы коллбэков ==========


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


class QueueSelection(CallbackData, prefix='queue'):
    """Класс коллбэков для выбора очереди публикаций"""
    chnl_id: int
    chnl_name: str


class TriggerSettings(CallbackData, prefix='trigger'):
    """Класс коллбэков для настройки очередей публикаций"""
    trigger_itself: str = 'None'
    interval: str = 'None'
    day_of_the_week: str = 'None'
    next_step: str = 'None'


class AddingPublication(CallbackData, prefix='add_post'):
    """Класс коллбэков для добавления публикаций"""
    publication_type: str


# ========== Сами клавиатуры ==========


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


async def queue_selection_keyboard():
    """Клавиатура для выбора очереди публикаций"""
    queues_keyboard = InlineKeyboardBuilder()
    channels_list = await db.get_channel_list()
    for channel in channels_list:
        queues_keyboard.button(text=channel['channel_name'],
                               callback_data=QueueSelection(
                                   chnl_id=channel['channel_id'],
                                   chnl_name=channel['channel_name']))
    queues_keyboard.adjust(1)
    return queues_keyboard.as_markup(resize_keyboard=True)


async def tr_set_keyboard(step):
    """Клавиатура для настройки очереди публикаций"""
    trigger_keyboard = InlineKeyboardBuilder()
    if step == 1:
        trigger_keyboard.button(text='По дням недели в определенное время',
                                callback_data=TriggerSettings(trigger_itself='cron'))
        trigger_keyboard.button(text='Определенными интервалами',
                                callback_data=TriggerSettings(trigger_itself='interval'))
        trigger_keyboard.adjust(1)
        return trigger_keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True)
    elif step == 2:
        # mon,tue,wed,thu,fri,sat,sun
        day_of_week = {'Понедельник': 'mon', 'Вторник': 'tue', 'Среда': 'wed',
                       'Четверг': 'thu', 'Пятница': 'fri', 'Суббота': 'sat', 'Воскресенье': 'sun', 'Каждый день': '*'}
        for day_key, day_value in day_of_week.items():
            trigger_keyboard.button(text=day_key, callback_data=TriggerSettings(day_of_the_week=day_value))
        trigger_keyboard.button(text='Отмена', callback_data=TriggerSettings(next_step='cancel'))
        trigger_keyboard.button(text='Дальше ➡️', callback_data=TriggerSettings(next_step='next_step'))
        trigger_keyboard.adjust(2)
        return trigger_keyboard.as_markup(resize_keyboard=True)


async def publication_type():
    """Клавиатура для выбора типа публикации"""
    post_type_keyboard = InlineKeyboardBuilder()
    types_dict = {'Текст': 'text', 'Картинка + Текст': 'pic_text', 'Картинка': 'pic', 'Видео + Текст': 'video_text',
                  'Видео': 'video', 'Видеосообщение': 'video_note', 'Файл + Текст': 'file_text', 'Файл': 'file'}

    for post_type, type_id in types_dict.items():
        post_type_keyboard.button(text=post_type, callback_data=AddingPublication(publication_type=type_id))
    post_type_keyboard.button(text='Отмена', callback_data=AddingPublication(publication_type='cancel'))

    post_type_keyboard.adjust(2)
    return post_type_keyboard.as_markup(resize_keyboard=True)


async def view_publications_list(page_dict):
    """Клавиатура для демонстрации публикаций из списка публикаций"""
    buttons = [
        [
            InlineKeyboardButton(text='🔎 Посмотреть медиафайл', callback_data='get_file')
        ],
        [
            InlineKeyboardButton(text='⬅️ Назад', callback_data='back_page'),
            InlineKeyboardButton(text=f'{page_dict["page"]}/{page_dict["count"]}', callback_data='empty'),
            InlineKeyboardButton(text='Вперед ➡️', callback_data='next_page')
        ],
        [
            InlineKeyboardButton(text='❌ Удалить публикацию', callback_data='start_delete')
        ]
    ]
    demonstration_keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return demonstration_keyboard


async def return_to_queue():
    """Кнопка для возврата из просмотра медиафайла обратно к очереди публикаций"""
    button = [[InlineKeyboardButton(text='Вернуться', callback_data='return')]]
    return InlineKeyboardMarkup(inline_keyboard=button)


async def deletion_confirmation():
    """Клавиатура для подтверждения удаления публикации"""
    buttons = [[
        InlineKeyboardButton(text='❌ Удалить', callback_data='delete'),
        InlineKeyboardButton(text='🚫 Отмена', callback_data='return')
    ]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
