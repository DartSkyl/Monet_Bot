from .Inline_keyboard.inline_for_admins import (
    del_board, SubDel,
    add_sub_keyboard, AddSubForUser,
    add_sub_channel_keyboard, SubAddForChannel,
    QueueSelection, TriggerSettings,
    queue_selection_keyboard, tr_set_keyboard)
from .reply_keyboard.admin_keyboard import (
    main_admin_keyboard,
    group_management,
    sub_manag,
    auto_posting,
    cancel_button,
    cancel_button_2
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
    "add_sub_channel_keyboard",
    "SubAddForChannel",
    "QueueSelection",
    "TriggerSettings",
    "queue_selection_keyboard",
    "tr_set_keyboard",
    "cancel_button_2",

    # пользовательские клавиатуры

    "main_user_keyboard"

)
