from utils import users_router
from keyboards import main_user_keyboard
from aiogram.types import Message
# from aiogram import F
from aiogram.filters import Command


@users_router.message(Command('start'))
async def user_start(msg: Message) -> None:
    await msg.answer("Добро пожаловать 😉\nВыберете действие:",
                     reply_markup=main_user_keyboard)
