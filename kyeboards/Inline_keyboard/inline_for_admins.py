from loader import subscription_dict, channels_dict, bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData


class SubDel(CallbackData, prefix='subdel'):
    """Класс коллбэков для удаления вариантов подписки"""
    sub_info: str


class AddSubForUser(CallbackData, prefix='addsub'):
    chl_id: int
    chl_name: str
    pass


def del_board():
    """Функция возвращает inline клавиатуру для удаления подписок"""
    sub_del_board = InlineKeyboardBuilder()
    for period, cost in sorted(subscription_dict.items()):
        if period != '0':  # Так как под этим ключом хранится пробный период
            button_text = f'Удалить подписку на {period} дней стоимость {str(cost)}'
            # Удалять будем по периоду, так как двух одинаковых периодов быть не может
            sub_del_board.button(text=button_text, callback_data=SubDel(sub_info=f'{period}'))
    sub_del_board.adjust(1)
    return sub_del_board.as_markup(resize_keyboard=True)


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
