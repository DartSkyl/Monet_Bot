from utils import admin_router, dict_queue
from states import AddingPost
from keyboards import (cancel_button, cancel_button_2, auto_posting,
                       queue_selection_keyboard, QueueSelection,
                       AddingPublication, publication_type)

from aiogram import F, html
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest


@admin_router.message(F.text == '➕ Добавить публикацию в очередь')
async def start_adding_publication(msg: Message, state: FSMContext):
    """Здесь начинается добавление публикации в очередь публикаций"""
    msg_text = 'Выберете очередь публикаций для добавления публикаций:'
    await msg.answer(text=msg_text, reply_markup=await queue_selection_keyboard())
    await state.set_state(AddingPost.step_one)


@admin_router.callback_query(QueueSelection.filter(), AddingPost.step_one)
async def adding_publication_choice_type(callback: CallbackQuery, callback_data: QueueSelection, state: FSMContext):
    """Здесь происходит выбор типа добавляемой публикации"""
    await callback.answer()
    msg_text = (f'Выбрана очередь публикаций <i><b>{html.quote(callback_data.chnl_name)}</b></i>\n'
                f'Выберете тип добавляемой публикации:')
    await callback.message.edit_text(text=msg_text, reply_markup=await publication_type())
    await state.set_state(AddingPost.step_two)


@admin_router.callback_query(AddingPublication.filter(), AddingPost.step_two)
async def adding_publication_input(callback: CallbackQuery, callback_data: AddingPublication, state: FSMContext):
    """Здесь происходит ввод содержимого будущей публикации"""
    await callback.answer()
    if callback_data.publication_type in ['text', 'pic_text', 'video_text', 'file_text']:
        msg_text = 'Введите текст будущей публикации:'
        await callback.message.edit_text(text=msg_text)
        await state.set_data({'selected_type': callback_data.publication_type})
        await state.set_state(AddingPost.step_three)
    elif callback_data.publication_type in ['pic', 'video', 'video_note', 'file']:
        msg_text = 'Загрузите файл будущей публикации:'
        await callback.message.edit_text(text=msg_text)
        await state.set_data({'selected_type': callback_data.publication_type})
        await state.set_state(AddingPost.step_three)
    else:  # Если пользователь нажал "Отмена"
        await state.clear()
        await callback.message.answer(text='Действие отменено', reply_markup=auto_posting)


@admin_router.message(AddingPost.step_three, F.text | F.photo | F.document | F.video | F.video_note)
async def adding_publication_get_content(msg: Message, state: FSMContext):
    """Здесь происходит загрузка контента пользователем"""
    content_type = (await state.get_data())['selected_type']
    # Проверяем, соответствует ли тип сброшенного контента заявленному
    if msg.text and content_type == 'text':

        print('Text')
    elif msg.photo and content_type in ['pic', 'pic_text']:
        print('Photo')
    elif msg.video and content_type in ['video', 'video_text']:
        print('Video')
    elif msg.document and content_type in ['file', 'file_text']:
        print('File')
    elif msg.video_note and content_type == 'video_note':
        print('Video note')
    else:
        print('Несовпадение типов')

