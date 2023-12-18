from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


kb_buttons = [
    [
        KeyboardButton(text='✅ Активировать пробную подписку'),
        KeyboardButton(text='ℹ️ Посмотреть подписку')
    ]
]

main_user_keyboard = ReplyKeyboardMarkup(
        keyboard=kb_buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
