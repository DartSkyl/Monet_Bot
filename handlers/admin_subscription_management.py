from loader import bot, db, channels_dict
from utils import admin_router

from aiogram.types import Message
from aiogram import F


@admin_router.message(F.text == '1')
async def test(msg: Message) -> None:
    print(channels_dict)
