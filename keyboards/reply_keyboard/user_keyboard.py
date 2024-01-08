from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


kb_buttons = [
        [KeyboardButton(text='🔎 Посмотреть доступные каналы')],
        [KeyboardButton(text='ℹ️ Информация о Вашей подписке')],
        [KeyboardButton(text='💳 Оплатить подписку')],
        [KeyboardButton(text='📨 Связаться с администрацией')]
]

main_user_keyboard = ReplyKeyboardMarkup(
        keyboard=kb_buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )


user_cancel = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='🚫 Отмена')]],
        resize_keyboard=True,
)
