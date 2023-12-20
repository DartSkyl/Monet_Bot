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
    await state.set_data({'channel_id': callback_data.chnl_id, 'channel_name': callback_data.chnl_name})
    await state.set_state(AddingPost.step_two)


@admin_router.callback_query(AddingPublication.filter(), AddingPost.step_two)
async def adding_publication_input(callback: CallbackQuery, callback_data: AddingPublication, state: FSMContext):
    """Здесь происходит ввод содержимого будущей публикации"""
    await callback.answer()

    if callback_data.publication_type in ['text',  'pic_text', 'video_text', 'file_text']:
        msg_text = 'Введите текст будущей публикации:'

        await callback.message.edit_text(text=msg_text)
        await state.update_data({'selected_type': callback_data.publication_type})
        await state.set_state(AddingPost.step_adding_text)

    elif callback_data.publication_type in ['pic', 'video', 'video_note', 'file']:
        msg_text = 'Загрузите файл будущей публикации:'

        await callback.message.edit_text(text=msg_text)
        await state.update_data({
            'selected_type': callback_data.publication_type,
            'text_for_post': 'empty'  # Эта заглушка нужна для конструкции ниже
        })
        await state.set_state(AddingPost.step_adding_file)

    else:  # Если пользователь нажал "Отмена"
        await state.clear()
        await callback.message.answer(text='Действие отменено', reply_markup=auto_posting)


@admin_router.message(AddingPost.step_adding_text, F.text)
async def adding_publication_get_text(msg: Message, state: FSMContext):
    """Здесь пользователь вводит текст для будущей публикации"""
    content_type = (await state.get_data())['selected_type']
    if content_type == 'text':
        if len(msg.text) <= 4096:
            channel_queue_id = (await state.get_data())['channel_id']
            msg_text = f'Публикация добавлена в очередь <i><b>{html.quote((await state.get_data())["channel_name"])}</b></i>'
            await dict_queue[channel_queue_id].adding_publication_in_queue(content_type=content_type, text=msg.text)
            await msg.answer(text=msg_text, reply_markup=auto_posting)
            await state.clear()
        else:
            await msg.answer(text=f'Ограничение для одного сообщения 4096 символа (Вы ввели {len(msg.text)} символа)',
                             reply_markup=cancel_button)
    else:
        if len(msg.text) <= 1024:
            await state.update_data({'text_for_post': msg.text})
            await state.set_state(AddingPost.step_adding_file)
            await msg.answer(text='Теперь скиньте файл', reply_markup=cancel_button)
        else:
            await msg.answer(text=f'Ограничение для описания файла 1024 символа (Вы ввели {len(msg.text)} символа)',
                             reply_markup=cancel_button)


@admin_router.message(AddingPost.step_adding_file, F.photo | F.document | F.video | F.video_note)
async def adding_publication_get_file(msg: Message, state: FSMContext):
    """Здесь пользователь скидывает файл будущей публикаций"""
    content_type = (await state.get_data())['selected_type']
    channel_queue_id = (await state.get_data())['channel_id']
    text_for_post = (await state.get_data())['text_for_post']
    msg_text = f'Публикация добавлена в очередь <i><b>{html.quote((await state.get_data())["channel_name"])}</b></i>'
    option_dict = {
        'video': (msg.video, None),
        'video_text': (msg.video, text_for_post),
        'file': (msg.document, None),
        'file_text': (msg.document, text_for_post),
        'video_note': (msg.video_note, None),
    }

    async def adding_post():
        await dict_queue[channel_queue_id].adding_publication_in_queue(
            content_type=content_type,
            file_id=option_dict[content_type][0].file_id,
            text=option_dict[content_type][1]
        )

        await msg.answer(text=msg_text, reply_markup=auto_posting)
        await state.clear()

    # Проверяем, соответствует ли тип сброшенного контента заявленному

    if msg.photo and content_type in ['pic', 'pic_text']:
        # Из-за того, что только msg.photo приходит в массиве, пришлось вынести эти ключи отдельно,
        # а иначе, при других типах сбрасываемого контента выскакивает ошибка
        option_dict['pic'] = (msg.photo[-1], None)
        option_dict['pic_text'] = (msg.photo[-1], text_for_post)
        await adding_post()

    elif msg.video and content_type in ['video', 'video_text']:
        await adding_post()

    elif msg.document and content_type in ['file', 'file_text']:
        await adding_post()

    elif msg.video_note and content_type == 'video_note':
        await adding_post()

    else:
        await msg.answer(text='Скинутый файл не соответствует заявленному', reply_markup=cancel_button)
