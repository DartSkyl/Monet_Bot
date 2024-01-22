from datetime import date, timedelta
from loader import db, bot
from utils import admin_router
from states import ViewStatistic
from keyboards import (cancel_button,
                       QueueSelection,  # Будем использовать клавиатуру для выбора очереди публикаций
                       queue_selection_keyboard,  # Так как функционал клавиатуры идеально подходит.
                       stat_period_markup, back_button, main_admin_keyboard)

from aiogram import F, html
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext


def data_processing(proc_data: list, date_interval: list, channel_name: str) -> str:
    """Функция принимает список со статистикой канала, а возвращает готовую строку"""
    money_received = 0
    is_member = 0
    trail_sub = 0
    left_channel = 0
    date_interval = ' - '.join(date_interval)

    for reporting_day in proc_data:
        money_received += reporting_day['money_received']
        is_member += reporting_day['is_member']
        trail_sub += reporting_day['trail_sub']
        left_channel += reporting_day['left_channel']

    ready_string = (f'Статистика канала <i><b>{html.quote(channel_name)}</b></i>\n'
                    f'Отчетный период: <b>{date_interval}</b>\n\n'
                    f'💵 Выручка: <b>{money_received}</b>\n'
                    f'🚹 Новых подписчиков: <b>{is_member}</b>\n'
                    f'🆓 Выдано пробных подписок: <b>{trail_sub}</b>\n'
                    f'🔕 Отписалось: <b>{left_channel}</b>')

    return ready_string


@admin_router.message(F.text == '📈 Статистика')
async def start_view_statistic(msg: Message, state: FSMContext):
    """Здесь начинается формирование показа статистики"""
    await state.set_state(ViewStatistic.begin)
    await msg.answer(text='Выберете канал для демонстрации статистики:', reply_markup=await queue_selection_keyboard())


@admin_router.callback_query(QueueSelection.filter(), ViewStatistic.begin)
async def choice_period_viewing(callback: CallbackQuery, callback_data: QueueSelection, state: FSMContext):
    """Хэндлер возвращает пользователю инлайн клавиатуру с выбором временного отрезка для просмотра статистики"""
    # Сразу сохраним выбор пользователя
    channel_name = (await bot.get_chat(callback_data.chnl_id)).title
    await state.set_data({'channel_id': callback_data.chnl_id, 'channel_name': channel_name})
    await callback.message.delete()
    await callback.message.answer(text='Теперь выберете промежуток времени для просмотра:',
                                  reply_markup=await stat_period_markup())
    await state.set_state(ViewStatistic.set_period)


@admin_router.callback_query(ViewStatistic.set_period)
async def set_statistic_period(callback: CallbackQuery, state: FSMContext):
    """Хэндлер достает из БД выбранного канала статистику за соответствующий период,
    формирует удобочитаемую строку и сообщением отравляет пользователю или предлагает ввести свой временной отрезок"""
    channel_info = await state.get_data()
    date_interval = {
        'week': [str(date.today() - timedelta(days=7)), str(date.today() - timedelta(days=1))],
        'month': [str(date.today() - timedelta(days=30)), str(date.today() - timedelta(days=1))],
    }
    stat_data = None  # Для дальнейшего использования
    msg_text = ''
    await callback.message.delete()
    if callback.data == 'today':
        stat_data = await db.get_today_statistic(channel_id=channel_info['channel_id'], date_today=str(date.today()))
        msg_text = data_processing(
            proc_data=stat_data,
            date_interval=[str(date.today())],
            channel_name=channel_info['channel_name']
        )
        await callback.message.answer(text=msg_text, reply_markup=back_button())

    elif callback.data in ['week', 'month']:
        # Получаем список со статистическими данными за выбранный период
        stat_data = await db.get_statistic_data(
            channel_id=channel_info['channel_id'],
            first_date=date_interval[callback.data][0],
            second_date=date_interval[callback.data][1]
        )
        msg_text = data_processing(
            proc_data=stat_data,
            date_interval=date_interval[callback.data],
            channel_name=channel_info['channel_name']
        )
        await callback.message.answer(text=msg_text, reply_markup=back_button())

    elif callback.data == 'all_days':
        stat_data = await db.get_statistic_for_all_period(channel_id=channel_info['channel_id'])
        msg_text = data_processing(
            proc_data=stat_data,
            date_interval=['За все время работы'],
            channel_name=channel_info['channel_name']
        )
        await callback.message.answer(text=msg_text, reply_markup=back_button())

    elif callback.data == 'user_date':
        await state.set_state(ViewStatistic.set_user_date)
        msg_text = ('Введите желаемый диапазон дат в формате\n"2024-01-01 2024-01-09"\n'
                    '<b>без кавычек и первая дата меньше второй‼️</b>')
        await callback.message.answer(text=msg_text, reply_markup=cancel_button)

    elif callback.data == 'go_back':

        await callback.message.answer(text='Выберете канал для демонстрации статистики:',
                                      reply_markup=await queue_selection_keyboard())
        await state.set_state(ViewStatistic.begin)

    elif callback.data == 'back':
        await callback.message.answer(text='Выберете промежуток времени для просмотра:',
                                      reply_markup=await stat_period_markup())


@admin_router.message(ViewStatistic.set_user_date, F.text.regexp(r'\d{4}-\d{2}-\d{2}\s\d{4}-\d{2}-\d{2}'))
async def get_user_date_interval(msg: Message, state: FSMContext):
    user_date = msg.text.split()
    channel_info = await state.get_data()
    stat_data = await db.get_statistic_data(
        channel_id=channel_info['channel_id'],
        first_date=user_date[0],
        second_date=user_date[1]
    )
    msg_text = data_processing(proc_data=stat_data, date_interval=user_date, channel_name=channel_info['channel_name'])
    await msg.answer(text=msg_text, reply_markup=back_button())
    await state.set_state(ViewStatistic.set_period)  # Что бы при нажатии кнопки "назад" вернутся назад


@admin_router.callback_query(ViewStatistic.begin, F.data == 'cancel')
async def stat_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена"""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(text='Действие отменено', reply_markup=main_admin_keyboard)
