from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


play = KeyboardButton(text='🎱 Бросить вызов фортуне!')
button_1 = KeyboardButton(text='✅ Активировать пробную подписку')
button_2 = KeyboardButton(text='ℹ️ Посмотреть подписку')
kb_buttons = [[play], [button_1], [button_2]]
playing_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=kb_buttons)
# playing_kb.add(play, button_1, button_2)
