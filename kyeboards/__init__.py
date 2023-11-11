from .Inline_keyboard.inline_for_admins import del_board, SubDel, add_sub_keyboard, AddSubForUser
from .reply_keyboard.admin_keyboard import (
    main_admin_keyboard,
    group_management,
    sub_manag,
    auto_posting,
    cancel_button
)
from .reply_keyboard.user_keyboard import main_user_keyboard

__all__ = (

    # клавиатуры администраторов

    "main_admin_keyboard",
    "group_management",
    "sub_manag",
    "auto_posting",
    "cancel_button",
    "del_board",
    "SubDel",
    "add_sub_keyboard",
    "AddSubForUser",

    # пользовательские клавиатуры

    "main_user_keyboard"

)
