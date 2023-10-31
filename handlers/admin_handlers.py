from loader import bot
from config_data.config import MAIN_GROUP_ID
from utils import admin_router

# Импорт всех клавиатур администратора
from kyeboards import (
    main_admin_keyboard,
    group_management,
    subscription_management,
    auto_posting
)

from aiogram.types import Message
from aiogram import F
from aiogram.filters import Command

# Что бы избежать нагромождения хэндлеров был реализован данный словарь.
# Где ключ это текст кнопки, а значение это вызываемая клавиатура

keyboards_dict = {
    '📝 Управление каналами': group_management,
    '⌛ Управление подписками': subscription_management,
    '📜 Авто постинг ': auto_posting,
    'Назад': main_admin_keyboard
}


@admin_router.message(Command('start'))
async def start(msg: Message) -> None:
    await msg.answer(f'Добро пожаловать, {msg.from_user.first_name}!'
                     f'\nВыберете действие:',
                     reply_markup=main_admin_keyboard)


@admin_router.message(Command('func'))
async def my_func(msg):
    result = await bot.get_chat(chat_id=MAIN_GROUP_ID)
    print(type(result))
    for elem in result:
        print(elem)


@admin_router.message(F.text.in_(keyboards_dict))
async def admins_menu(msg: Message) -> None:
    """ Хэндлер реализует навигацию по администраторскому меню через словарь"""

    await msg.answer(text='Выберете операцию:', reply_markup=keyboards_dict[msg.text])

# @admin_router.message(Command("ban"))
# async  def handing_message(msg):
#     await bot.ban_chat_member(chat_id=-1001513097504, user_id=6724839493)
#
#
# @admin_router.message(Command("unban"))
# async  def handing_message(msg):
#     await bot.unban_chat_member(chat_id=-1001513097504, user_id=6724839493)


# @admin_router.message(F.forward_from.as_('reply'))
# async def member_info(reply_msg: Message, reply):
#     print(reply.id)
