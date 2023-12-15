from loader import bot, db, channels_dict
from utils import admin_router, add_queue, delete_queue, SubManag
from states import GroupManagementStates as GMS

# Импорт всех клавиатур администратора
from kyeboards import (
    main_admin_keyboard,
    group_management,
    sub_manag,
    auto_posting,
    cancel_button
)

from aiogram.types import Message
from aiogram import F, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from asyncpg.exceptions import UniqueViolationError

# Что бы избежать нагромождения хэндлеров и конструкций if else был реализован данный словарь.
# Где ключ это текст кнопки, а значение это вызываемая клавиатура

keyboards_dict = {
    '📝 Управление каналами': group_management,
    '⌛ Управление подписками': sub_manag,
    '📜 Авто постинг': auto_posting,
    'Назад': main_admin_keyboard
}


@admin_router.message(Command('start'))
async def start(msg: Message, state: FSMContext) -> None:
    await msg.answer(f'Добро пожаловать, <b>{msg.from_user.first_name}</b>!'
                     f'\nВыберете действие:',
                     reply_markup=main_admin_keyboard)
    await state.clear()


@admin_router.message(F.text.in_(keyboards_dict))
async def admins_menu(msg: Message, state: FSMContext) -> None:
    """ Хэндлер реализует навигацию по администраторскому меню через словарь"""

    await msg.answer(text='Выберете операцию:', reply_markup=keyboards_dict[msg.text])
    await state.clear()


@admin_router.message(F.text == "📃 Список каналов")
async def get_channels_list(msg: Message) -> None:
    """Хэндлер выводит список каналов находящихся в БД"""
    ch_list = await db.get_channel_list()
    fr_chn = ""
    pd_chn = ""
    for elem in ch_list:
        if elem['is_paid']:
            pd_chn += f"Название - <i>{html.quote(elem['channel_name'])}</i>   ID: <b>{elem['channel_id']}</b>\n"
        else:
            fr_chn += f"Название - <i>{html.quote(elem['channel_name'])}</i>   ID: <b>{elem['channel_id']}</b>\n"
    msg_ch_list = ("Список каналов:\n"
                   "\nОткрытые:\n"
                   f"{fr_chn}"
                   "\nЗакрытые:\n"
                   f"{pd_chn}")
    await msg.answer(text=msg_ch_list)


@admin_router.message(F.text.in_({'➕ Добавить открытый канал', '➕➕ Добавить закрытый канал'}))
async def free_channel_add(msg: Message, state: FSMContext):
    """Хэндлер добавления каналов в БД"""

    await state.set_state(GMS.adding_channel)

    # С помощью флага будем помечать какую группу добавляют
    if msg.text == '➕ Добавить открытый канал':
        await state.set_data({'paid': False})
    else:
        await state.set_data({'paid': True})

    await msg.answer("Введите ID канала\n"
                     "ID канала должно быть <b>целым отрицательным числом!</b>\n"
                     "Пример: -1001972569167\n"
                     "Если вы не знаете ID канала, то перешлите любой пост из этого канала боту "
                     "@LeadConverterToolkitBot\n"
                     " (https://t.me/LeadConverterToolkitBot)", reply_markup=cancel_button)


@admin_router.message(GMS.adding_channel, F.text.regexp(r'-\d{8,}'))
async def adding_free_ch(msg: Message, state: FSMContext):
    """Хэндлер ловит ID добавляемой группы. Проверка корректности ввода идет через регулярное выражение.
    Не знаю какой разброс количества чисел в ID в телеграмме, по этому поставил так"""

    try:
        paid = await state.get_data()  # Флаг, в виде словаря, помещаем в отдельную переменную для передачи в БД
        added_ch = await bot.get_chat(chat_id=int(msg.text))
        await db.add_channel(channel_id=added_ch.id, channel_name=added_ch.title, paid=paid['paid'])
        # Так же добавляем канал в оперативную память
        if paid['paid']:
            channels_dict['is_paid'].append(added_ch.id)
            # И сразу создадим для канала отдельную таблицу,
            # что бы контролировать подписки пользователей
            await db.add_channel_table(int(msg.text))
            await add_queue(int(msg.text))
        else:
            channels_dict['free'].append(added_ch.id)
            await add_queue(int(msg.text))

        reply_msg_text = ("Канал добавлен!\n"
                          f"Название канала - {html.bold(html.quote(added_ch.title))}\n")
        await msg.answer(text=reply_msg_text, reply_markup=main_admin_keyboard)
        await state.clear()

    except TelegramBadRequest as exc:
        # Данное исключение будет вызвано если канала с таким ID не существует
        # или бот не добавлен в качестве администратора
        await msg.answer(text='Канал с таким ID не найден или бот не является администратором данного канала!\n'
                              'Уточните ID канала и повторите попытку', reply_markup=cancel_button)
        await state.set_state(GMS.adding_channel)  # Устанавливаем стэйт заново

    except UniqueViolationError as exc:
        # Данное исключение будет вызвано если канал с таким ID уже есть в базе данных
        await msg.answer(text='Канал с таким ID уже добавлен!')
        await state.set_state(GMS.adding_channel)  # Устанавливаем стэйт заново


@admin_router.message(F.text == '➖ Удалить канал')
async def channel_delete(msg: Message, state: FSMContext) -> None:
    """Хэндлер запускает процесс удаление канала"""
    del_msg = ("Введите ID канала\n"
               "ID канала должно быть <b>целым отрицательным числом</b>!\n"
               "Пример: -1001972569167\n"
               "ID каналов доступных для удаления можно посмотреть в <i><b>'Списке каналов'</b></i>")
    await msg.answer(text=del_msg, reply_markup=cancel_button)
    await state.set_state(GMS.deleting_channel)


@admin_router.message(GMS.deleting_channel, F.text.regexp(r'-\d{8,}'))
async def delete_channel(msg: Message, state: FSMContext) -> None:
    """Хэндлер удаления канала"""
    try:

        # Сделаем список с ID каналов доступных для удаления
        ch_id_list = [ch_id['channel_id'] for ch_id in await db.get_channel_list()]

        if int(msg.text) in ch_id_list:  # Проверим, есть ли такой ID в списке
            await db.delete_channel(channel_id=int(msg.text))
            # Так же удаляем из оперативной памяти
            if int(msg.text) in channels_dict['free']:
                channels_dict['free'].remove(int(msg.text))
            else:
                channels_dict['is_paid'].remove(int(msg.text))
                await db.delete_channel_table(int(msg.text))
                await SubManag.clear_channel_subscription(int(msg.text))
            await delete_queue(int(msg.text))
        else:
            raise ValueError

        await msg.answer(text='Канал удален!', reply_markup=main_admin_keyboard)
        await state.clear()
    except ValueError:
        await msg.answer(text="Канала с таким ID в базе нет!\n", reply_markup=cancel_button)


@admin_router.message(F.text == '🚫 Отмена')
async def cancel_action(msg: Message, state: FSMContext):
    """Хэндлер отмены действия с установленным стэйтом"""
    await state.clear()
    await msg.answer(text='Действие отменено!', reply_markup=main_admin_keyboard)


@admin_router.message(GMS.adding_channel)
async def error_input(msg: Message):
    """Хэндлер отлавливает некорректный ввод при добавлении канала"""
    await msg.answer(text="Не корректный ввод!\n"
                          "ID канала должно быть <b>целым отрицательным числом!</b>\n"
                          "Пример: -1001972569167\n", reply_markup=cancel_button)


@admin_router.message(GMS.deleting_channel)
async def error_input(msg: Message):
    """Хэндлер отлавливает некорректный ввод при удалении канала"""
    await msg.answer(text="Не корректный ввод!\n"
                          "ID канала должно быть <b>целым отрицательным числом!</b>\n"
                          "Пример: -1001972569167\n", reply_markup=cancel_button)
