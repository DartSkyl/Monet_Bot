from utils import admin_router, dict_queue
from states import AutoPost
from keyboards import (auto_posting, queue_selection_keyboard, cancel_button,
                       cancel_button_2, QueueSelection, view_publications_list)

from aiogram import F, html
from aiogram.types import Message, CallbackQuery
from aiogram.types.input_media_photo import InputMediaPhoto
from aiogram.types.input_media_video import InputMediaVideo
from aiogram.types.input_media_document import InputMediaDocument
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup


# option_dict = {
#         'pic': ...,
#         'pic_text': ...,
#         'video': (msg.video, None),
#         'video_text': (msg.video, text_for_post),
#         'file': (msg.document, None),
#         'file_text': (msg.document, text_for_post),
#         'video_note': (msg.video_note, None),
#     }


@admin_router.message(F.text == '📅 Посмотреть очередь публикаций')
async def publish_queue(message: Message, state: FSMContext):
    """Активирует просмотр очередей публикаций"""
    select_keyboard = await queue_selection_keyboard()
    await message.answer(text='Выберете очередь публикаций для просмотра:', reply_markup=select_keyboard)
    await state.set_state(AutoPost.check_queue)


@admin_router.callback_query(QueueSelection.filter(), AutoPost.check_queue)
async def start_demonstration_queue(callback: CallbackQuery, callback_data: QueueSelection, state: FSMContext):
    """Здесь стартует показ очереди публикаций"""
    await callback.answer()
    msg_text = await dict_queue[callback_data.chnl_id].get_queue_info(callback_data.chnl_name)
    await callback.message.answer(text=msg_text)
    await callback.message.delete()
    try:
        list_of_publication = await dict_queue[callback_data.chnl_id].get_list_publication()
        first_publication = list_of_publication[0]
        post_type = first_publication.get_type()
        file_id = first_publication.get_file_id()
        post_text = first_publication.get_text()
        # Сначала зададим необходимые значения, что бы ориентироваться по списку публикаций
        await state.set_data({'count': len(list_of_publication), 'page': 1})
        # И сразу же сделаем из них словарь, что бы передать их для создания клавиатуры
        page = await state.get_data()

        if post_type == 'text':
            await callback.message.answer(text=post_text,
                                          reply_markup=await view_publications_list(page_dict=page))
        elif post_type in ['pic', 'pic_text']:
            await callback.message.answer_photo(photo=file_id, caption=post_text,
                                                reply_markup=await view_publications_list(page_dict=page))
        elif post_type in ['video', 'video_text']:
            await callback.message.answer_video(video=file_id, caption=post_text,
                                                reply_markup=await view_publications_list(page_dict=page))
        elif post_type in ['file', 'file_text']:
            await callback.message.answer_document(document=file_id, caption=post_text,
                                                   reply_markup=await view_publications_list(page_dict=page))
        elif post_type == 'video_note':
            await callback.message.answer_video_note(video_note=file_id,
                                                     reply_markup=await view_publications_list(page_dict=page))

        await state.set_state(AutoPost.view_publications)
        await state.update_data({'channel_id': callback_data.chnl_id})

    except IndexError:  # Если список публикаций пуст
        await callback.message.answer(text='Очередь публикаций пуста', reply_markup=auto_posting)
        await state.clear()


@admin_router.callback_query(AutoPost.view_publications, F.data.in_(['next_page', 'back_page']))
async def queue_demonstration(callback: CallbackQuery, state: FSMContext):
    """Здесь основная функция показа очереди публикаций"""
    channel_id = (await state.get_data())['channel_id']

    # Здесь так же есть ключ 'channel_id', но нам это не помешает, так что будем его игнорировать
    page = await state.get_data()
    display_publication_index = page['page'] - 1  # Очевидно, так как нумерация страниц начинается с 1, а индекса с 0

    list_of_publication = await dict_queue[channel_id].get_list_publication()
    if callback.data == 'next_page':
        next_publication = list_of_publication[display_publication_index + 1]
        page['page'] += 1  # И сразу меняем номер страницы
        post_type = next_publication.get_type()
        file_id = next_publication.get_file_id()
        post_text = next_publication.get_text()
        if post_type == 'text':
            await callback.message.edit_text(text=post_text,
                                             reply_markup=await view_publications_list(page_dict=page))
        # else:
        #     await callback.message.edit_media(media=, caption=post_text,
        #                                       reply_markup=await view_publications_list(page_dict=page))
            # await callback.message.answer_video_note()
