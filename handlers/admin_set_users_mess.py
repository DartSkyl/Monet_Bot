from loader import users_mess_dict, db
from utils import admin_router
from states import UsersMessages
from keyboards import (redactor_for_message, users_system_messages,
                       cancel_button, main_admin_keyboard, users_msg_markup, QueueSelection,
                       channels_messages_markup)

from aiogram import F, html
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext


@admin_router.message(F.text == '⚙️ Настройка пользовательских сообщений')
async def start_set_users_mess(msg: Message):
    """Здесь стартует настройка или просмотр пользовательских сообщений"""
    await msg.answer(text='Выберете опцию:', reply_markup=users_msg_markup)


@admin_router.message(F.text == '📄 Системные сообщения')
async def system_messages(msg: Message, state: FSMContext):
    """Начало настройки системных сообщений"""
    await state.set_state(UsersMessages.set_system_mess)
    await msg.answer(text='Выберете сообщение', reply_markup=await users_system_messages())


@admin_router.message(F.text == '📝 Описание каналов')
async def channels_messages(msg: Message, state: FSMContext):
    """Начало настройки описания каналов"""
    await state.set_state(UsersMessages.set_channel_mess)
    await msg.answer(text='Описание какого канала будем настраивать?', reply_markup=await channels_messages_markup())


@admin_router.callback_query(UsersMessages.set_system_mess, F.data == 'go_back')
async def back_to_system_messages(callback: CallbackQuery):
    """Здесь возврат к системным сообщениям"""
    await callback.message.delete()
    await callback.message.answer(text='Выберете сообщение:', reply_markup=await users_system_messages())


@admin_router.callback_query(UsersMessages.set_channel_mess, F.data == 'go_back')
async def back_to_channels_messages(callback: CallbackQuery):
    """Здесь возврат к описаниям каналов"""
    await callback.message.delete()
    await callback.message.answer(text='Описание какого канала будем настраивать?',
                                  reply_markup=await channels_messages_markup())


@admin_router.callback_query(UsersMessages.set_system_mess, F.data == 'edit')
async def edit_users_message(callback: CallbackQuery, state: FSMContext):
    """Здесь мы редактируем системное сообщение"""
    await callback.answer()
    await state.set_state(UsersMessages.edit_mess)
    await callback.message.answer(text='Введите новый текст сообщения:', reply_markup=cancel_button)


@admin_router.callback_query(UsersMessages.set_channel_mess, F.data == 'edit')
async def edit_users_message(callback: CallbackQuery, state: FSMContext):
    """Здесь мы редактируем описание канала"""
    await callback.answer()
    await state.set_state(UsersMessages.edit_channel_mess)
    await callback.message.answer(text='Введите новое описание канала:', reply_markup=cancel_button)


@admin_router.callback_query(UsersMessages.set_channel_mess, QueueSelection.filter())
async def get_channels_mess(callback: CallbackQuery, callback_data: QueueSelection, state: FSMContext):
    """Здесь происходит вывод установленного описания канала"""
    await callback.message.delete()
    await state.set_data({'message': str(callback_data.chnl_id)})  # Сразу сохраним выбор пользователя

    msg_text = f'Описание для канала: <b>{html.quote(callback_data.chnl_name)}</b>\n'
    msg_text += '<i>Не установлено</i>' if not users_mess_dict.get(str(callback_data.chnl_id))\
        else users_mess_dict[str(callback_data.chnl_id)]  # Если у ключа есть значение, то его и вставим

    await callback.message.answer(text=msg_text, reply_markup=await redactor_for_message())


@admin_router.callback_query(UsersMessages.set_system_mess, F.data.in_(
    ['hi_mess', 'paid', 'trail_sub', 'not_trail', 'was_trail', 'sub_end', 'sub_stop']
))
async def get_users_mess(callback: CallbackQuery, state: FSMContext):
    """Здесь происходит вывод уже установленных пользовательских сообщений"""
    dict_for_msg = {
        'hi_mess': 'Приветственное сообщение',
        'paid': 'Сообщение после оплаты',
        'trail_sub': 'Сообщение пробной подписки',
        'not_trail': 'Сообщение, если пробной подписки нет',
        'was_trail': 'Сообщение, если пробная подписка уже выдавалась',
        'sub_end': 'Сообщение для заканчивающийся подписки',
        'sub_stop': 'Сообщение, когда подписка закончилась',
    }
    await callback.message.delete()
    await state.set_data({'message': callback.data})  # Сразу сохраним выбор пользователя
    msg_text = f'<b>{dict_for_msg[callback.data]}:</b>\n{users_mess_dict[callback.data]}'
    await callback.message.answer(text=msg_text, reply_markup=await redactor_for_message())


@admin_router.message(UsersMessages.edit_channel_mess)
async def set_message(msg: Message, state: FSMContext):
    """Здесь сохраняется описание канала"""
    edit_mess = (await state.get_data())['message']  # Берем заранее сохраненный ключ выбранного сообщения
    users_mess_dict[edit_mess] = msg.text  # Описание каналов будут храниться под ключом из строки своего ID
    await db.set_users_messages(mess_for=edit_mess, mess_text=msg.text)
    await msg.answer(text='Сообщение сохранено',reply_markup=main_admin_keyboard)
    await state.clear()


@admin_router.message(UsersMessages.edit_mess)
async def set_message(msg: Message, state: FSMContext):
    """Здесь измененное сообщение сохраняется"""
    edit_mess = (await state.get_data())['message']  # Берем заранее сохраненный ключ выбранного сообщения
    users_mess_dict[edit_mess] = msg.text
    await db.set_users_messages(mess_for=edit_mess, mess_text=msg.text)
    await msg.answer(text='Сообщение сохранено',reply_markup=main_admin_keyboard)
    await state.clear()


@admin_router.message(F.text == '📩 Установить контакт для подписчиков')
async def set_contact(msg: Message, state: FSMContext):
    """Здесь задаем стэйт для установки контакта для подписчиков"""
    await state.set_state(UsersMessages.set_admin_contact)
    await msg.answer(text='Введите @UserName администратора:', reply_markup=cancel_button)


@admin_router.message(UsersMessages.set_admin_contact, F.text.regexp(r'@\w{5,32}'))
async def get_admin_username(msg: Message, state: FSMContext):
    """Здесь ловим юзернэйм администратора"""
    await db.set_users_messages(mess_for='admin_username', mess_text=msg.text)
    users_mess_dict['admin_username'] = msg.text
    await msg.answer(text='Контакт сохранен', reply_markup=users_msg_markup)
    await state.clear()


@admin_router.message(UsersMessages.set_admin_contact)
async def error_input_username(msg: Message):
    """Сообщаем о некорректности ввода"""
    await msg.answer(text='Неверный ввод!')


@admin_router.callback_query(UsersMessages.set_system_mess, F.data == 'cancel')
async def cancel_set_mess(callback: CallbackQuery, state: FSMContext):
    """Здесь отмена"""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(text='Действие отменено', reply_markup=main_admin_keyboard)


@admin_router.callback_query(UsersMessages.set_channel_mess, F.data == 'cancel')
async def cancel_set_mess(callback: CallbackQuery, state: FSMContext):
    """Здесь отмена"""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(text='Действие отменено', reply_markup=main_admin_keyboard)
