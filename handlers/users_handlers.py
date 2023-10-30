from utils import users_router
from aiogram.types import Message
# from aiogram import F
from aiogram.filters import Command


@users_router.message(Command('start'))
async def user_start(msg: Message) -> None:
    await msg.answer("Вы не можете бросить вызов фортуне!\n"
                     "А я могу😜")
