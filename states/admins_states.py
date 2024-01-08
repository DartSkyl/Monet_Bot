from aiogram.fsm.state import StatesGroup, State


class GroupManagementStates(StatesGroup):
    """Класс содержит стэйты для управления каналами"""
    adding_channel = State()
    deleting_channel = State()


class SubscriptionManagement(StatesGroup):
    """Класс содержит стэйты для управления подписками"""
    set_trail_sub = State()
    set_paid_sub = State()
    add_subscription_a_user = State()


class AutoPost(StatesGroup):
    """Класс содержит стэйты для настройки очереди публикаций"""
    set_trigger_step_one = State()
    set_trigger_step_two = State()
    set_trigger_day = State()
    set_trigger_time = State()
    set_trigger_interval = State()
    check_queue = State()
    view_publications = State()
    queue_switch = State()


class AddingPost(StatesGroup):
    """Класс содержит стэйты для добавления постов в очередь публикаций"""
    step_one = State()
    step_two = State()
    step_adding_text = State()
    step_adding_file = State()
    step_three = State()  # ?
    step_four = State()  # ?
    false_state = State()


class UsersMessages(StatesGroup):
    """Класс содержит стэйты для установки пользовательских сообщений"""
    set_system_mess = State()
    set_channel_mess = State()
    edit_mess = State()
    edit_channel_mess = State()
    set_admin_contact = State()
