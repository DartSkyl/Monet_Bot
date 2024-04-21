import asyncio
import re
from loader import bot
from utils import admin_router, dict_queue
from states import AddingPost
from keyboards import (cancel_button, auto_posting,
                       queue_selection_keyboard, QueueSelection,
                       only_file, only_text)

from aiogram import F, html
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext


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
    channel_name = (await bot.get_chat(callback_data.chnl_id)).title
    msg_text = (f'Выбрана очередь публикаций <i><b>{html.quote(channel_name)}</b></i>\n'
                f'Публикация может быть трех видов:\n'
                f'- только текст (3000 символов)\n'
                f'- текст (1024 символа) + файл(ы)(до 10 файлов)\n'
                f'- только файл(ы)(до 10 файлов)\n\n'
                f'Скиньте файл(ы) или нажмите кнопку <b>Дальше</b>')
    await callback.message.answer(text=msg_text, reply_markup=only_text)
    await state.set_data({'channel_id': callback_data.chnl_id, 'channel_name': channel_name, 'mediafile': []})
    await state.set_state(AddingPost.step_adding_file)


@admin_router.message(AddingPost.step_adding_file, F.text != 'Дальше')
async def adding_files(msg: Message, state: FSMContext):
    """Здесь пользователь добавляет файл(ы) в будущую публикацию"""

    # Так как, при скидывании более одного файла, бот воспринимает это сразу как несколько отдельных
    # сообщений, то будем использовать эту причудливую конструкцию с заранее созданным списком

    file_id_list = (await state.get_data())['mediafile']

    if msg.photo:
        file_id_list.append((msg.photo[-1].file_id, 'photo'))
    elif msg.video:
        file_id_list.append((msg.video.file_id, 'video'))
    elif msg.document:
        file_id_list.append((msg.document.file_id, 'document'))
    elif msg.video_note:
        file_id_list.append((msg.video_note.file_id, 'video_note'))

    await state.update_data({'mediafile': file_id_list})


@admin_router.message(AddingPost.step_adding_file, F.text == 'Дальше')
async def check_file(msg: Message, state: FSMContext):
    """Проверяем файлы, которые скинул пользователь. Если все нормально, то предлагаем ввести текст"""
    file_id_list = (await state.get_data())['mediafile']

    # Если файлов больше чем надо, то просим повторить
    if 0 < len(file_id_list) <= 10:
        type_set = {t[1] for t in file_id_list}

        # Проверяем на однотипность добавленных файлов. Вперемешку могут быть только фото и видео(не видеосообщение)

        if len(type_set) == 1:  # значит, что у передаваемых файлов один тип
            await msg.answer(text='Теперь введите текст или нажмите кнопу Готово:', reply_markup=only_file)
            await state.set_state(AddingPost.step_adding_text)
            await state.update_data({'only_text': False})
        elif len(type_set) == 2 and ('photo' and 'video' in type_set):
            await msg.answer(text='Теперь введите текст или нажмите кнопу Готово:', reply_markup=only_file)
            await state.set_state(AddingPost.step_adding_text)
            await state.update_data({'only_text': False})
        else:
            await msg.answer(text='Файлы должны быть однотипными! Совместно можно только фото и видео!',
                             reply_markup=only_text)
            await state.update_data({'mediafile': []})

    elif len(file_id_list) == 0:  # Значит только текст
        await state.set_state(AddingPost.step_adding_text)
        await msg.answer(text='Введите текст', reply_markup=cancel_button)
        await state.update_data({'only_text': True})

    else:
        await msg.answer(text='Фалов слишком много, повторите попытку', reply_markup=only_text)
        await state.update_data({'mediafile': []})


@admin_router.message(AddingPost.step_adding_text, F.text != '🚫 Отмена')
async def adding_publication_get_text(msg: Message, state: FSMContext):
    """Здесь пользователь вводит текст для будущей публикации"""
    if '<' in msg.text:
        await msg.answer(text=html.quote('Использование символа "<" в тексте нельзя, так как это нарушит работу бота!'))
    else:

        post_info = await state.get_data()
        channel_queue_id = post_info['channel_id']
        channel_queue_name = post_info['channel_name']
        msg_text = f'Публикация добавлена в очередь <i><b>{html.quote(channel_queue_name)}</b></i>'
        enti = msg.entities  # Для ссылок внутри текста
        text_for_post = msg.text
        try:
            for elem in enti:
                if elem.type == 'text_link':
                    reg = r'[^#]{0}'.format(elem.extract_from(msg.text))
                    sub_str = f'<a href = "{elem.url}">{elem.extract_from(msg.text)}</a>'
                    text_for_post = re.sub(reg, sub_str, text_for_post)
        except TypeError:
            pass

        if post_info['only_text']:
            if len(msg.text) <= 3000:

                await dict_queue[channel_queue_id].adding_publication_in_queue(text=text_for_post)
                await msg.answer(text=msg_text, reply_markup=auto_posting)
                await state.clear()
            else:
                await state.set_state(AddingPost.false_state)  # Это нужно для того, что бы когда телеграмм разобьет
                # сообщение на две части не пропустить второе

                await msg.answer(text=f'Ограничение для одного сообщения 3000 символов '
                                      f'(Вы ввели {len(msg.text)} символа)',
                                 reply_markup=only_file)

                await asyncio.sleep(1)
                await state.set_state(AddingPost.step_adding_text)  # И сразу установим стэйт обратно,
                # что бы пользователь мог повторить ввод текста для публикации
        else:
            if len(msg.text) <= 1024:
                # file_id_list = [i[0] for i in post_info['mediafile']]
                await dict_queue[channel_queue_id].adding_publication_in_queue(
                    text=(text_for_post if msg.text != 'Готово' else None),
                    file_id=post_info['mediafile']
                )
                await msg.answer(text=msg_text, reply_markup=auto_posting)
                await state.clear()

            else:
                await msg.answer(text=f'Ограничение для описания файла(ов) 1024 символа '
                                      f'(Вы ввели {len(msg.text)} символа)',
                                 reply_markup=only_file)
