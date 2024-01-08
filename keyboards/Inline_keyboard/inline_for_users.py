from loader import subscription_dict, channels_dict, bot, db
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData


class ChannelsSelection(CallbackData, prefix='chnls'):
    """Коллбэк для выбора канала подписчиком"""
    channel_id: int
    channel_name: str


class ChannelsForPayment(CallbackData, prefix='pay'):
    """Коллбэк для выбора канала подписчиком"""
    channel_id: int
    channel_name: str


class SubscriptionSelection(CallbackData, prefix='sub'):
    """Коллбэк для выбора подписки"""
    period: int
    cost: int


async def channels_selection():
    """Клавиатура для выбора доступных каналов"""
    channels_list = await db.get_channel_list()
    channels_selection_markup = InlineKeyboardBuilder()
    for channel in channels_list:
        channels_selection_markup.button(text=channel['channel_name'],
                                         callback_data=ChannelsSelection(
                                             channel_id=channel['channel_id'],
                                             channel_name=channel['channel_name']
                                         ))
    channels_selection_markup.button(text='🚫 Отмена', callback_data='cancel')
    channels_selection_markup.adjust(1)
    return channels_selection_markup.as_markup(resize_keyboard=True)


async def channels_for_payment():
    """Клавиатура для выбора доступных каналов"""
    channels_list = await db.get_paid_channels_list()
    channels_selection_markup = InlineKeyboardBuilder()
    for channel in channels_list:
        channels_selection_markup.button(text=channel['channel_name'],
                                         callback_data=ChannelsForPayment(
                                             channel_id=channel['channel_id'],
                                             channel_name=channel['channel_name']
                                         ))
    channels_selection_markup.button(text='🚫 Отмена', callback_data='cancel')
    channels_selection_markup.adjust(1)
    return channels_selection_markup.as_markup(resize_keyboard=True)


async def view_description(chnl_url):
    """Кнопки для возврата к списку каналов и для перехода в сам канал"""
    buttons = [
        [InlineKeyboardButton(text='Перейти в канал ➡️', url=chnl_url)],
        [InlineKeyboardButton(text='⏪ Вернуться', callback_data='go_back')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def subscription_keyboard(sub_dict):
    """Клавиатура для выбора подписки"""
    sub_keyboard = InlineKeyboardBuilder()
    for period, cost in sorted(sub_dict.items()):
        if period != 0:
            sub_keyboard.button(text=f'Срок: {period} дня/дней, стоимость: {cost}',
                                callback_data=SubscriptionSelection(period=period, cost=cost))
    sub_keyboard.button(text='🚫 Отмена', callback_data='cancel')
    sub_keyboard.adjust(1)
    return sub_keyboard.as_markup()
