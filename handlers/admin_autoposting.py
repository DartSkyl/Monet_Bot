from utils import admin_router, dict_queue
from states import AutoPost
from kyeboards import (auto_posting, queue_selection_keyboard, tr_set_keyboard, cancel_button,
                       cancel_button_2, QueueSelection, TriggerSettings)

from aiogram import F, html
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

week = {'mon': 'Понедельник', 'tue': 'Вторник', 'wed': 'Среда', 'thu': 'Четверг',
        'fri': 'Пятница', 'sat': 'Суббота', 'sun': 'Воскресенье', '*': 'Каждый день'}


@admin_router.message(Command('start'))
async def start(message: Message):
    await message.answer('Bot ready!', reply_markup=auto_posting)


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


# ==========Настройка очереди публикаций ==========


@admin_router.message(F.text == '⚙️ Настройка очереди публикаций')
async def trigger_settings_start(message: Message, state: FSMContext):
    """Запускает настройку триггера для отдельно взятой очереди публикаций"""
    select_keyboard = await queue_selection_keyboard()
    await message.answer(text='Выберете очередь публикаций какого канала вы хотите настроить:',
                         reply_markup=select_keyboard)
    await state.set_state(AutoPost.set_trigger_step_one)


@admin_router.callback_query(QueueSelection.filter(), AutoPost.set_trigger_step_one)
async def trigger_settings_step_one(callback: CallbackQuery, callback_data: QueueSelection, state: FSMContext):
    """После выбора канала для настройки очереди публикаций, дает на выбор основной принцип работы для очереди.
    Один из двух вариантов: по дням недели в определенное время и интервалами"""
    await callback.answer()
    await state.set_data({'channel': (callback_data.chnl_id, callback_data.chnl_name)})
    trigger_keyboard = await tr_set_keyboard(1)
    msg_text = (f'Настройка очереди публикаций для канала <i><b>{html.quote(callback_data.chnl_name)}</b></i>\n'
                '\nВыберете основной принцип по которому будет работать очередь публикаций:')
    await callback.message.edit_text(text=msg_text, reply_markup=trigger_keyboard)
    await state.set_state(AutoPost.set_trigger_step_two)


@admin_router.callback_query(TriggerSettings.filter(), AutoPost.set_trigger_step_two)
async def trigger_settings_step_two(callback: CallbackQuery, callback_data: TriggerSettings, state: FSMContext):
    """В зависимости от выбора на предыдущем шаге активирует дальнейшую настройку
    триггера: либо выбор дней недели, либо интервал"""
    await state.update_data({'trigger': callback_data.trigger_itself})
    chnl_info = await state.get_data()
    if callback_data.trigger_itself == 'cron':
        msg_text = (f'Настройка очереди публикаций для канала <i><b>{html.quote(chnl_info["channel"][1])}</b></i>\n'
                    'Принцип работы очереди: <b>По дням недели в определенное время</b>\n'
                    '\nВыберете дни:')
        await callback.message.edit_text(text=msg_text, reply_markup=await tr_set_keyboard(2))
        await state.update_data({'days': []})
        await state.set_state(AutoPost.set_trigger_day)
    elif callback_data.trigger_itself == 'interval':
        msg_text = (f'Настройка очереди публикаций для канала <i><b>{html.quote(chnl_info["channel"][1])}</b></i>\n'
                    'Принцип работы очереди: <b>Определенными интервалами</b>\n\n'
                    'Введите временной интервал в формате <b>"1:00"</b> без кавычек\n')
        await state.set_state(AutoPost.set_trigger_interval)
        await callback.message.edit_text(text=msg_text)
        await callback.message.answer(text='‼️Максимально допустимый интервал 96:00 (96 часов или 4-о суток)',
                                      reply_markup=cancel_button)


@admin_router.callback_query(TriggerSettings.filter(), AutoPost.set_trigger_day)
async def trigger_setting_day(callback: CallbackQuery, callback_data: TriggerSettings, state: FSMContext):
    """Активируется при настройке очереди публикаций по дням недели"""
    if callback_data.next_step != 'next_step' and callback_data.next_step != 'cancel':
        await callback.answer()
        chnl_info = (await state.get_data())['channel']
        days = (await state.get_data())['days']
        if callback_data.day_of_the_week not in days and '*' not in days:
            if len(days) < 6 and callback_data.day_of_the_week != '*':
                days.append(callback_data.day_of_the_week)
            else:
                days = ['*']
        await state.update_data({'days': days})
        days_for_msg = ''
        for day in days:
            days_for_msg += week[day] + ' '
        msg_text = (f'Настройка очереди публикаций для канала <i><b>{html.quote(chnl_info[1])}</b></i>\n'
                    'Принцип работы очереди: <b>По дням недели в определенное время</b>\n'
                    f'\nВыбранные дни: <b>{days_for_msg}</b>\n'
                    f'\nВыберете дни или нажмите <b>Дальше>></b>:')
        try:
            await callback.message.edit_text(text=msg_text, reply_markup=await tr_set_keyboard(2))
        except TelegramBadRequest as exc:
            print(exc)

    elif callback_data.next_step == 'next_step':
        if len((await state.get_data())['days']) > 0:
            text_for_msg_1 = 'Введите время для публикации в формате <b>"15:30"</b> без кавычек'
            text_for_msg_2 = '‼️Ввод простого числа, например <b>17</b>, эквивалентен <b>"17:00"</b>\n'
            await state.set_state(AutoPost.set_trigger_time)
            await callback.message.edit_text(text=text_for_msg_1)
            await callback.message.answer(text=text_for_msg_2, reply_markup=cancel_button)
            await state.update_data({'time': []})
        else:
            await callback.answer(text='Выберете хотя бы один день')
    elif callback_data.next_step == 'cancel':
        await callback.message.edit_text('Настройка очереди публикаций <i><b>отменена</b></i>')
        await state.clear()


@admin_router.message(AutoPost.set_trigger_time, F.text.regexp(r'\d{1,2}[:]\d{2}$|\d{1,2}$'))
async def trigger_setting_time(msg: Message, state: FSMContext):
    """Активирует ввод и захват времени для публикации постов по дням недели"""
    user_time = msg.text.split(':')
    added_time = (await state.get_data())['time']
    if len(user_time) > 1:
        if 0 <= int(user_time[0]) <= 23 and 0 <= int(user_time[1]) <= 59:
            added_time.append(msg.text)
            await state.update_data({'time': added_time})
        else:
            await msg.answer(text='Такого времени не существует, как минимум на нашей планете!')
    else:
        if 0 <= int(user_time[0]) <= 23:
            added_time.append(msg.text + ':00')
            await state.update_data({'time': added_time})
        else:
            await msg.answer(text='Такого времени не существует, как минимум на нашей планете!')
    time_values = ''
    for tm in added_time:
        time_values += tm + ', '
    msg_text = (f'Список времени для публикации постов: <b>{time_values}</b>\n'
                f'Введите время еще или нажмите <b>"Готово"</b>')
    await msg.answer(text=msg_text, reply_markup=cancel_button_2)


@admin_router.message(AutoPost.set_trigger_time, F.text == '✔️ Готово')
async def trigger_setting_done(msg: Message, state: FSMContext):
    """Завершает настройку очереди публикаций по дням недели, сохраняет настройки и выводит их для пользователя"""
    trigger_info = await state.get_data()
    selected_days = ''
    selected_time = ''
    for day in trigger_info['days']:
        selected_days += week[day] + ' '
    for tm in trigger_info['time']:
        selected_time += tm + ' '
    trigger_info_msg = (
        f'Настройки очереди публикаций\nдля канала <i><b>{html.quote(trigger_info["channel"][1])}</b></i>:\n'
        f'Основной принцип работы: <b>По дням недели</b>\n'
        f'Выбранные дни: <b>{selected_days}</b>\n'
        f'Выбранное время: <b>{selected_time}</b>'
    )

    dict_queue[trigger_info['channel'][0]].queue_info = '_'.join([selected_days, selected_time])
    await dict_queue[trigger_info['channel'][0]].save_trigger_setting([trigger_info['days'], trigger_info['time']])
    await dict_queue[trigger_info['channel'][0]].set_trigger()

    await msg.answer(text=trigger_info_msg, reply_markup=auto_posting)
    await state.clear()


@admin_router.message(AutoPost.set_trigger_interval, F.text.regexp(r'\d{1,2}[:]\d{2}$'))
async def trigger_setting_interval(msg: Message, state: FSMContext):
    """Здесь происходит установка временного интервала для очереди публикаций"""
    user_time = msg.text.split(':')
    if 0 <= int(user_time[0]) <= 96 and 0 <= int(user_time[1]) <= 59:
        msg_text = (f'Установленный интервал очереди публикаций\nдля канала '
                    f'<i><b>{html.quote((await state.get_data())["channel"][1])}</b></i>:\n'
                    f'<b>{user_time[0]}</b> час(ов) <b>{user_time[1]}</b> минут')
        await state.update_data({'time_interval': msg.text})
        await msg.answer(text=msg_text, reply_markup=auto_posting)
        chn_info = await state.get_data()

        dict_queue[chn_info['channel'][0]].queue_info = msg.text
        await dict_queue[chn_info['channel'][0]].save_trigger_setting(msg.text)
        await dict_queue[chn_info['channel'][0]].set_trigger()

        await state.clear()
    else:
        await msg.answer(text='Слишком большой интервал! Оно тебе надо?')


@admin_router.message(AutoPost.set_trigger_time)
async def trigger_setting_error_input(msg: Message):
    await msg.answer(text='Неверный ввод!')


@admin_router.message(AutoPost.set_trigger_interval)
async def trigger_setting_error_input(msg: Message):
    await msg.answer(text='Неверный ввод!')

