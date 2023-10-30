from loader import dp, bot
from utils import admin_router
from kyeboards.reply_keyboard.admin_keyboard import playing_kb
from aiogram.types import Message
# from aiogram import F
from aiogram.filters import Command


@admin_router.message(Command('start'))
async def start(msg: Message) -> None:
    await msg.answer('Добро пожаловать! Выберете действие:', reply_markup=playing_kb)


@admin_router.message(lambda msg: msg.text == '🎱 Бросить вызов фортуне!')
async def start_2(msg: Message) -> None:
    await msg.answer_dice()
