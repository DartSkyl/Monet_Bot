from aiogram.fsm.state import StatesGroup, State


class UserPayment(StatesGroup):
    """Стэйт для оплаты подписки"""
    choice_channel = State()
    choice_period = State()
    payment = State()


class CommunicationAdministration(StatesGroup):
    """Для связи с администраторами"""
    write_message = State()
