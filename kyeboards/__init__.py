from .reply_keyboard.admin_keyboard import (
    main_admin_keyboard,
    group_management,
    subscription_management,
    auto_posting,
    cancel_button
)
from .reply_keyboard.user_keyboard import main_user_keyboard

__all__ = (

    # клавиатуры администраторов

    "main_admin_keyboard",
    "group_management",
    "subscription_management",
    "auto_posting",
    "cancel_button",

    # пользовательские клавиатуры

    "main_user_keyboard"

)
