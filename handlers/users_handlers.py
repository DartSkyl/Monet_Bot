from loader import users_mess_dict
from utils import users_router
from keyboards import main_user_keyboard
from aiogram.types import Message
from aiogram import F
from aiogram.filters import Command


@users_router.message(Command('start'))
async def user_start(msg: Message) -> None:
    """Здесь начинается взаимодействие с пользователем"""
    await msg.answer(text=users_mess_dict['hi_mess'],
                     reply_markup=main_user_keyboard)


@users_router.message(F.text == '🔎 Посмотреть доступные каналы')
async def looking_channels(msg: Message):
    """Здесь выводим список доступных каналов. И платных, и нет"""
    pass


@users_router.message(F.text == 'ℹ️ Информация о Вашей подписке')
async def get_subscription_info(msg: Message):
    """Здесь выводится информация о всех имеющихся подписках"""
    pass


@users_router.message(F.text == '💳 Оплатить подписку')
async def pay_for_subscription(msg: Message):
    """САМАЯ ВАЖНАЯ ЧАСТЬ. Ради нее все и делалось! Здесь мы принимаем оплату от подписчиков
    за подписку и накидываем время оплаченной подписки"""
    pass


@users_router.message(F.text == '📨 Связаться с администрацией')
async def communication_with_the_administration(msg: Message):
    """Здесь происходит связь с администрацией"""
    pass
