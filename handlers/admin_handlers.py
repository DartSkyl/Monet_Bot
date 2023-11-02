from loader import bot, db
from config_data.config import MAIN_GROUP_ID
from utils import admin_router
from states import GroupManagementStates as GMS

# Импорт всех клавиатур администратора
from kyeboards import (
    main_admin_keyboard,
    group_management,
    subscription_management,
    auto_posting,
    cancel_button
)

from aiogram.types import Message
from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from asyncpg.exceptions import UniqueViolationError

# Что бы избежать нагромождения хэндлеров был реализован данный словарь.
# Где ключ это текст кнопки, а значение это вызываемая клавиатура

keyboards_dict = {
    '📝 Управление каналами': group_management,
    '⌛ Управление подписками': subscription_management,
    '📜 Авто постинг ': auto_posting,
    'Назад': main_admin_keyboard
}


@admin_router.message(Command('start'))
async def start(msg: Message) -> None:
    await msg.answer(f'Добро пожаловать, {msg.from_user.first_name}!'
                     f'\nВыберете действие:',
                     reply_markup=main_admin_keyboard)


@admin_router.message(Command('func'))
async def my_func(msg):
    result = await bot.get_chat(chat_id=MAIN_GROUP_ID)
    await msg.answer('Check the result!')
    print(type(result))
    for elem in result:
        print(elem)


@admin_router.message(F.text.in_(keyboards_dict))
async def admins_menu(msg: Message) -> None:
    """ Хэндлер реализует навигацию по администраторскому меню через словарь"""

    await msg.answer(text='Выберете операцию:', reply_markup=keyboards_dict[msg.text])


@admin_router.message(F.text.in_({'➕ Добавить открытый канал', '➕➕ Добавить закрытый канал'}) )
async def free_channel_add(msg: Message, state: FSMContext):
    """Хэндлер добавления каналов в базу данных"""

    await state.set_state(GMS.adding_channel)

    # С помощью флага будем помечать какую группу добавляют
    if msg.text == '➕ Добавить открытый канал':
        await state.set_data({'paid': False})
    else:
        await state.set_data({'paid': True})

    await msg.answer("Введите ID канала\n"
                     "ID канала должно быть целый отрицательным числом!\n"
                     "Пример: -1001972569167\n"
                     "Если вы не знаете ID канала, то перешлите любой пост из этого канала боту "
                     "@LeadConverterToolkitBot\n"
                     " (https://t.me/LeadConverterToolkitBot)", reply_markup=cancel_button)


@admin_router.message(GMS.adding_channel, F.text.regexp(r'-\d{8,}'))
async def adding_free_ch(msg: Message, state: FSMContext):
    """Хэндлер ловит ID добавляемой группы. Проверка корректности ввода идет через регулярное выражение.
    Не знаю какой разброс количества чисел в ID в телеграмме, по этому поставил так"""

    try:
        paid = await state.get_data()
        await state.clear()
        added_ch = await bot.get_chat(chat_id=int(msg.text))
        await db.add_channel(channel_id=added_ch.id, channel_name=added_ch.title, paid=paid['paid'])

        reply_msg_text = ("Канал добавлен!\n"
                          f"Название канала - {added_ch.title}\n")
        await msg.answer(text=reply_msg_text, reply_markup=main_admin_keyboard)

    except TelegramBadRequest as exc:
        # Данное исключение будет вызвано если канала с таким ID не существует
        await msg.answer(text='Канал с таким ID не найден или бот не является администратором данного канала!\n'
                              'Уточните ID канала и повторите попытку', reply_markup=cancel_button)
        await state.set_state(GMS.adding_channel)  # Устанавливаем стэйт заново
        print(exc)

    except UniqueViolationError as exc:
        # Данное исключение будет вызвано если канал с таким ID уже есть в базе данных
        await msg.answer(text='Канал с таким ID уже добавлен!')
        await state.set_state(GMS.adding_channel)  # Устанавливаем стэйт заново
        print(exc)


@admin_router.message(GMS.adding_channel, F.text == '🚫 Отмена')
async def cancel_action(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(text='Действие отменено!', reply_markup=main_admin_keyboard)


@admin_router.message(GMS.adding_channel)
async def error_input(msg: Message):
    await msg.answer(text="Не корректный ввод!\n"
                          "ID канала должно быть целый отрицательным числом!\n"
                          "Пример: -1001972569167\n", reply_markup=cancel_button)












# @admin_router.message(Command("ban"))
# async  def handing_message(msg):
#     await bot.ban_chat_member(chat_id=-1001513097504, user_id=6724839493)
#
#
# @admin_router.message(Command("unban"))
# async  def handing_message(msg):
#     await bot.unban_chat_member(chat_id=-1001513097504, user_id=6724839493)


# @admin_router.message(F.forward_from.as_('reply'))
# async def member_info(reply_msg: Message, reply):
#     print(reply.id)
