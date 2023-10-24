from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


playing_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
play = KeyboardButton('🎱 Бросить вызов фортуне!')
button_1 = KeyboardButton('✅ Активировать пробную подписку')
button_2 = KeyboardButton('ℹ️ Посмотреть подписку')

playing_kb.add(play, button_1, button_2)
