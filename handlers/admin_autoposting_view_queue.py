from utils import admin_router, dict_queue
from states import AutoPost
from kyeboards import (auto_posting, queue_selection_keyboard, cancel_button,
                       cancel_button_2, QueueSelection)

from aiogram import F, html
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest


@admin_router.message(F.text == '📅 Посмотреть очередь публикаций')
async def publish_queue(message: Message, state: FSMContext):
    """Активирует просмотр очередей публикаций"""
    select_keyboard = await queue_selection_keyboard()
    await message.answer(text='Выберете очередь публикаций для просмотра:', reply_markup=select_keyboard)
    await state.set_state(AutoPost.check_queue)


@admin_router.callback_query(QueueSelection.filter(), AutoPost.check_queue)
async def check_queue(callback: CallbackQuery, callback_data: QueueSelection, state: FSMContext):
    await callback.answer()
    msg_text = await dict_queue[callback_data.chnl_id].get_queue_info(callback_data.chnl_name)
    await callback.message.answer(text=msg_text)
