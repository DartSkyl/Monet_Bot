from .Inline_keyboard.inline_for_admins import (
    del_board, SubDel,
    add_sub_keyboard, AddSubForUser,
    add_sub_channel_keyboard, SubAddForChannel,
    QueueSelection, TriggerSettings,
    queue_selection_keyboard, tr_set_keyboard,
    AddingPublication, publication_type,
    view_publications_list, return_to_queue,
    deletion_confirmation, SwitchQueue, switch_keyboard,
    users_system_messages, redactor_for_message, channels_messages_markup,
    stat_period_markup, back_button)

from .Inline_keyboard.inline_for_users import (
    channels_selection, view_description, ChannelsSelection,
    subscription_keyboard, SubscriptionSelection,
    ChannelsForPayment, channels_for_payment
)
from .reply_keyboard.admin_keyboard import (
    main_admin_keyboard,
    group_management,
    sub_manag,
    auto_posting,
    cancel_button,
    cancel_button_2,
    returning_button, users_msg_markup,
    only_text, only_file
)
from .reply_keyboard.user_keyboard import main_user_keyboard, user_cancel

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
    "AddingPublication",
    "publication_type",
    "view_publications_list",
    "return_to_queue",
    "deletion_confirmation",
    "returning_button",
    "SwitchQueue",
    "switch_keyboard",
    "users_system_messages",
    "redactor_for_message",
    "users_msg_markup",
    "channels_messages_markup",
    "stat_period_markup",
    "back_button",
    "only_text",
    "only_file",

    # пользовательские клавиатуры

    "main_user_keyboard",
    "channels_selection",
    "view_description",
    "ChannelsSelection",
    "subscription_keyboard",
    "SubscriptionSelection",
    "ChannelsForPayment",
    "channels_for_payment",
    "user_cancel"
)
