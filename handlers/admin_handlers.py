from loader import dp, bot
from database.base import group_create
from kyeboards.reply_keyboard.admin_keyboard import playing_kb
from aiogram.types import Message


@dp.message_handler(commands=['start'])
async def start(msg: Message) -> None:
    await msg.answer('Добро пожаловать! Выберете действие:', reply_markup=playing_kb)


@dp.message_handler(lambda msg: msg.text == '🎱 Бросить вызов фортуне!')
async def start_2(msg: Message) -> None:
    m = await msg.answer_dice()
    print(m.dice.value)

@dp.message_handler(lambda msg:msg.text == 'создать группу')
async def make_group(message: Message) -> None:
    msg: Message = await bot.send_message(message.from_user.id, text='Скерстил пальчики?')
    await group_create("test_table")
