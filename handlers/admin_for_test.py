from aiogram.filters import Command
from aiogram.types import Message
from loader import dp, admins_id


@dp.message(Command('as_admin'))
async def add_in_admin_for_test(msg: Message):
    """Функция добавляет пользователя в список администраторов"""
    admins_id.append(msg.from_user.id)
    await msg.answer('Вы стали администратором бота и можете ознакомиться с его функционалом!'
                     '\nВведите команду /start для обновления интерфейса\n'
                     '<b>Данная функция присутствует только в тестовом режиме❗</b>')


@dp.message(Command('as_user'))
async def return_to_user_state(msg: Message):
    """Функция возвращает в состояние пользователя"""
    admins_id.remove(msg.from_user.id)
    await msg.answer('Вы перестали быть администратором бота и можете посмотреть на бота глазами '
                     'простого подписчика\nВведите команду /start для обновления интерфейса\n'
                     '<b>Данная функция присутствует только в тестовом режиме❗</b>')
