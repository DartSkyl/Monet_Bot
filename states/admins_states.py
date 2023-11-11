from aiogram.fsm.state import StatesGroup, State


class GroupManagementStates(StatesGroup):
    """Класс содержит стэйты для управления каналами"""
    adding_channel = State()  # Стэйт добавления канала
    deleting_channel = State()  # Стэйт удаления канала


class SubscriptionManagement(StatesGroup):
    """Класс содержит стэйты для управления подписками"""
    set_trail_sub = State()  # Стэйт установки пробной подписки
    set_paid_sub = State()  # Стэйт установки платной подписки
    add_subscription_a_user = State()  # Стэйт для добавления подписки пользователю
