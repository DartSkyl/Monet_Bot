from loader import users_mess_dict, db
from utils import admin_router
from states import UsersMessages
from keyboards import redactor_for_message, users_messages, cancel_button, main_admin_keyboard
from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext


@admin_router.message(F.text == '⚙️ Настройка пользовательских сообщений')
async def start_set_users_mess(msg: Message, state: FSMContext):
    """Здесь стартует настройка или просмотр пользовательских сообщений"""
    await msg.answer(text='Выберете сообщение:', reply_markup=await users_messages())
    await state.set_state(UsersMessages.set_mess)


@admin_router.callback_query(UsersMessages.set_mess, F.data == 'go_back')
async def back_to_messages(callback: CallbackQuery, state: FSMContext):
    """Здесь возврат к сообщениям"""
    await callback.message.delete()
    await callback.message.answer(text='Выберете сообщение:', reply_markup=await users_messages())


@admin_router.callback_query(UsersMessages.set_mess, F.data == 'edit')
async def edit_users_message(callback: CallbackQuery, state: FSMContext):
    """Здесь мы редактируем сообщение"""
    await callback.answer()
    await state.set_state(UsersMessages.edit_mess)
    await callback.message.answer(text='Введите новый текст сообщения:', reply_markup=cancel_button)


@admin_router.callback_query(UsersMessages.set_mess, F.data == 'cancel')
async def cancel_set_mess(callback: CallbackQuery, state: FSMContext):
    """Здесь отмена"""
    await callback.message.delete()
    await callback.message.answer(text='Действие отменено', reply_markup=main_admin_keyboard)


@admin_router.callback_query(UsersMessages.set_mess)
async def get_users_mess(callback: CallbackQuery, state: FSMContext):
    """Здесь происходит вывод уже установленных пользовательских сообщений"""
    dict_for_msg = {
        'hi_mess': 'Приветственное сообщение',
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


@admin_router.message(UsersMessages.edit_mess)
async def set_message(msg: Message, state: FSMContext):
    """Здесь измененное сообщение сохраняется"""
    edit_mess = (await state.get_data())['message']  # Берем заранее сохраненный ключ выбранного сообщения
    users_mess_dict[edit_mess] = msg.text
    await db.set_users_messages(mess_for=edit_mess, mess_text=msg.text)
    await msg.answer(text='Сообщение сохранено',reply_markup=main_admin_keyboard)
    await state.clear()
