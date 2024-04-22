from aiogram.utils.media_group import MediaGroupBuilder

from utils import admin_router, dict_queue
from states import AutoPost
from loader import bot
from keyboards import (auto_posting, queue_selection_keyboard,
                       QueueSelection, view_publications_list,
                       deletion_confirmation, returning_button)

from aiogram import F
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
async def start_demonstration_queue(callback: CallbackQuery, callback_data: QueueSelection, state: FSMContext):
    """Здесь стартует показ очереди публикаций"""
    await callback.answer()
    channel_name = (await bot.get_chat(callback_data.chnl_id)).title
    msg_text = await dict_queue[callback_data.chnl_id].get_queue_info(channel_name)
    await callback.message.answer(text=msg_text, reply_markup=returning_button)
    await callback.message.delete()
    try:
        list_of_publication = await dict_queue[callback_data.chnl_id].get_list_publication()
        first_publication = list_of_publication[0]
        publication_info = first_publication.get_info()
        # Сначала зададим необходимые значения, что бы ориентироваться по списку публикаций
        await state.set_data({'count': len(list_of_publication), 'page': 1})
        # И сразу же сделаем из них словарь, что бы передать их для создания клавиатуры
        page = await state.get_data()

        await callback.message.answer(text=publication_info, reply_markup=await view_publications_list(page))

        await state.set_state(AutoPost.view_publications)
        await state.update_data({'channel_id': callback_data.chnl_id, 'publication': first_publication})

    except IndexError:  # Если список публикаций пуст
        await callback.message.answer(text='<b>Очередь публикаций пуста!</b>', reply_markup=auto_posting)
        await state.clear()


@admin_router.callback_query(AutoPost.view_publications, F.data.in_(['next_page', 'back_page']))
async def queue_demonstration(callback: CallbackQuery, state: FSMContext):
    """Здесь основная функция показа очереди публикаций"""
    channel_id = (await state.get_data())['channel_id']

    # Здесь так же есть еще несколько ключей, но нам это не помешает, будем использовать только 'page' и 'count'
    page = await state.get_data()
    display_publication_index = page['page'] - 1  # Очевидно, так как нумерация страниц начинается с 1, а индекса с 0
    next_publication = None  # Дальше здесь будет контейнер с публикацией
    list_of_publication = await dict_queue[channel_id].get_list_publication()
    page['count'] = len(list_of_publication)  # На случай, если во время просмотра что-нибудь опубликовалось
    try:
        if callback.data == 'next_page':
            if display_publication_index < (page['count'] - 1):
                next_publication = list_of_publication[display_publication_index + 1]
                page['page'] += 1  # И сразу меняем номер страницы
            else:
                # Если дойдя до конца пользователь листает вперед,
                # то переключаем на первую публикацию
                next_publication = list_of_publication[0]
                page['page'] = 1

        elif callback.data == 'back_page':
            if display_publication_index > 0:
                next_publication = list_of_publication[display_publication_index - 1]
                page['page'] -= 1  # И сразу меняем номер страницы
            else:
                # Если с самого начала листают назад,
                # то переключаемся на последнюю публикацию в списке
                next_publication = list_of_publication[page['count'] - 1]
                page['page'] = page['count']
    except IndexError:
        # Если в очереди осталась одна запись и во время просмотра она опубликовалась,
        # а пользователь решил полистать. Да маразм! И что?
        await callback.message.delete()
        await callback.message.answer(text='<b>Очередь публикаций пуста!</b>', reply_markup=auto_posting)
        await state.clear()

    try:
        await callback.message.edit_text(text=next_publication.get_info(),
                                         reply_markup=await view_publications_list(page))

        await state.update_data({  # Сохраним изменения для дальнейшего использования
            'page': page['page'],
            'publication': next_publication  # Нужно для демонстрации медиафайла
        })

    except TelegramBadRequest:
        # Выскочит, если в списке публикаций только одна запись и пользователь будет листать. Заигнорим
        pass
    except AttributeError:
        # Выскочит, если "маразм" сработает
        pass


@admin_router.callback_query(AutoPost.view_publications, F.data == 'get_file')
async def show_mediafile(callback: CallbackQuery, state: FSMContext):
    """Здесь происходит демонстрация медиафайла публикации, если таковой имеется"""
    publication_files = (await state.get_data())['publication'].get_file_id()
    if publication_files:  # Если списка, значит объявление без медиафайлов
        await callback.answer()
        if publication_files[0][1] in {'photo', 'video', 'audio', 'document'}:
            media_group = MediaGroupBuilder()
            for mediafile in publication_files:
                media_group.add(type=mediafile[1], media=mediafile[0])
            await bot.send_media_group(chat_id=callback.from_user.id, media=media_group.build())
            await state.set_state(AutoPost.file_demonstration)
        else:
            if publication_files[0][1] == 'voice':
                await bot.send_voice(chat_id=callback.from_user.id, voice=publication_files[0][0])
                await state.set_state(AutoPost.file_demonstration)
            elif publication_files[0][1] == 'video_note':
                await bot.send_video_note(chat_id=callback.from_user.id, video_note=publication_files[0][0])
                await state.set_state(AutoPost.file_demonstration)
    else:
        await callback.answer(text='Публикация не содержит медиафайла!')


@admin_router.message(F.text == '⏪ Вернуться', AutoPost.file_demonstration)
async def return_from_file_demonstration(msg: Message, state: FSMContext):
    """Здесь мы возвращаемся из просмотра файлов"""
    publication = (await state.get_data())['publication']
    page = await state.get_data()
    await state.set_state(AutoPost.view_publications)
    await msg.answer(text=publication.get_info(), reply_markup=await view_publications_list(page))


@admin_router.callback_query(AutoPost.view_publications, F.data == 'return')
async def return_to_view_queue(callback: CallbackQuery, state: FSMContext):
    """Здесь мы возвращаемся при отмене удаления публикации к просмотру очереди"""
    await callback.message.delete()
    publication = (await state.get_data())['publication']
    page = await state.get_data()
    await callback.message.answer(text=publication.get_info(), reply_markup=await view_publications_list(page))


@admin_router.callback_query(AutoPost.view_publications, F.data == 'start_delete')
async def start_deleting_publication(callback: CallbackQuery):
    """Здесь пользователь подтверждает или отменяет удаление публикации"""
    await callback.message.delete()
    await callback.message.answer(text='‼️Подтвердите удаления публикации‼️',
                                  reply_markup=await deletion_confirmation())


@admin_router.callback_query(AutoPost.view_publications, F.data == 'delete')
async def delete_publication(callback: CallbackQuery, state: FSMContext):
    """Здесь происходит удаление публикации из очереди публикаций"""

    publication_info = await state.get_data()  # Для удобства скинем все в один словарь

    # Индекс удаляемой публикации это page['page'] - 1
    post_to_be_deleted_index = publication_info['page'] - 1
    queue = dict_queue[publication_info['channel_id']]
    await queue.remove_publication(post_to_be_deleted_index)

    # Теперь изменим значения page['page'] и page['count']
    if publication_info['page'] == publication_info['count']:
        publication_info['page'] -= 1
    publication_info['count'] -= 1
    await state.update_data({
        'page': publication_info['page'],
        'count': publication_info['count']
    })

    # И обновим показ очереди публикаций
    if publication_info['count'] > 0:
        publication = (await queue.get_list_publication())[publication_info['page'] - 1]
        await callback.message.edit_text(text=publication.get_info(),
                                         reply_markup=await view_publications_list(publication_info))
    else:
        await callback.message.delete()
        await callback.message.answer(text='<b>Очередь публикаций пуста!</b>', reply_markup=auto_posting)
        await state.clear()


@admin_router.message(F.text == '⏪ Вернуться', AutoPost.view_publications)
async def return_to_autoposting_menu(msg: Message, state: FSMContext):
    """Здесь пользователь возвращается в меню автопостинга"""
    await state.clear()
    await msg.answer(text='Просмотр публикаций прекращен', reply_markup=auto_posting)
