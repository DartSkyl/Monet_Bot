import time
from loader import bot, channels_dict, subscription_dict, db
from utils import admin_router, SubManag
from states import SubscriptionManagement as SM
from kyeboards import (
    cancel_button, main_admin_keyboard,
    sub_manag, del_board, SubDel,
    add_sub_keyboard, AddSubForUser,
    add_sub_channel_keyboard, SubAddForChannel)
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram import F, html


@admin_router.message(F.text == '2')
async def test2(msg):
    print(channels_dict)


@admin_router.message(F.text == '⚙️ Посмотреть/удалить установленные подписки')
async def check_sub_settings(msg: Message) -> None:
    """Хэндлер выводит актуальную информацию по подпискам"""
    paid_chn_list = await db.get_paid_channels_list()
    sub_text = ''
    for elem in paid_chn_list:
        chn_name = ('<i>==========</i>\n<i><b>' + html.quote(elem['channel_name']) + '</b></i>:\n')
        sub_text += chn_name
        for period, cost in sorted(subscription_dict[elem['channel_id']].items()):
            if period == 0:
                sub_text += (f'Пробный период {int(cost / (60 * 60 * 24))} дня/дней\n' if (cost / (60 * 60 * 24)) > 0
                             else 'Пробная подписка отключена\n')
            else:
                sub_text += f'Подписка на {period} дня/дней, стоимость {cost} рублей\n'

    await msg.answer(text=sub_text, reply_markup=del_board(paid_chn_list))


@admin_router.callback_query(SubDel.filter())
async def sub_delete(callback: CallbackQuery, callback_data: SubDel) -> None:
    """Хэндлер реагирует на нажатие кнопки inline клавиатуры для удаления вариантов подписки.
    Результатом реакции является изменения сообщения и клавиатуры"""
    await SubManag.delete_subscription(chl_id=callback_data.chnl_id, period=callback_data.sub_period)
    await callback.answer()
    edit_text = ''
    paid_chn_list = await db.get_paid_channels_list()
    for elem in paid_chn_list:
        chn_name = ('<i>==========</i>\n<i><b>' + html.quote(elem['channel_name']) + '</b></i>:\n')
        edit_text += chn_name
        for period, cost in sorted(subscription_dict[elem['channel_id']].items()):
            if period == 0:
                edit_text += (f'Пробный период {int(cost / (60 * 60 * 24))} дня/дней\n' if (cost / (60 * 60 * 24)) > 0
                              else 'Пробная подписка отключена\n')
            else:
                edit_text += f'Подписка на {period} дня/дней, стоимость {cost} рублей\n'

    await callback.message.edit_text(text=edit_text, reply_markup=del_board(paid_chn_list))


@admin_router.message(F.text == '💵 Добавить платную подписку')
async def set_paid_sub_step_1(msg: Message, state: FSMContext) -> None:
    """Хэндлер запускает стэйт добавления варианта платной подписки"""
    m_text = ('Введите желаемый срок подписки и стоимость через пробел\n'
              '<i><b>Пример:</b></i> подписка на 30 дней стоимостью 100 рублей - "30 100" <b>без кавычек!</b>')
    # m_text = 'Выберете канал для добавления подписки:'
    # sub_keyboard = await add_sub_channel_keyboard()
    await msg.answer(text=m_text, reply_markup=cancel_button)
    await state.set_state(SM.set_paid_sub)


@admin_router.message(SM.set_paid_sub, F.text.regexp(r'\d{1,}\s\d{1,}$'))
async def set_paid_sub_step_2(msg: Message, state: FSMContext) -> None:
    """В хэндлере происходит выбор канала, на который происходит добавление варианта платной подписки"""
    sub_set = msg.text.split()
    if int(sub_set[0]) > 0:
        await state.set_data({'sub_info': [sub_set[0], int(sub_set[1])]})
        ms_text = 'Выберете, на какой канал добавить данный вариант подписки:'
        sub_keyboard = await add_sub_channel_keyboard()
        await msg.answer(text=ms_text, reply_markup=sub_keyboard)
    else:
        await msg.answer(text='Подписка на 0 дней? Давай еще раз попробуем!', reply_markup=cancel_button)


@admin_router.callback_query(SubAddForChannel.filter(), SM.set_paid_sub)
async def set_paid_sub_step_3(callback: CallbackQuery, callback_data: SubAddForChannel, state: FSMContext) -> None:
    """Хэндлер завершает добавление платного варианта подписки"""
    sub_set = await state.get_data()
    await SubManag.set_paid_subscription(
        channel_id=int(callback_data.chn_id),
        period=sub_set['sub_info'][0],
        cost=sub_set['sub_info'][1]
    )
    await callback.answer()
    ans_text = (f'Подписка на канал <i><b>{html.quote(callback_data.chn_name)}</b></i>\n'
                f'стоимостью <i><b>{sub_set["sub_info"][1]} рублей</b></i> \n'
                f'сроком на <i><b>{sub_set["sub_info"][0]}</b></i> дня/дней добавлена!')
    await callback.message.answer(text=ans_text, reply_markup=sub_manag)
    await state.clear()


@admin_router.message(F.text == '⏲️ Изменить период пробной подписки')
async def set_trail_subscription(msg: Message, state: FSMContext) -> None:
    """Хэндлер запускает состояние изменения пробной подписки"""
    await state.set_state(SM.set_trail_sub)
    await msg.answer(text="Введите количество дней для пробной подписки\n"
                          "Что бы отключить пробную подписку введите 0", reply_markup=cancel_button)


@admin_router.message(SM.set_trail_sub, F.text.regexp(r'\d{1,}'))
async def set_trail_subscription_period(msg: Message, state: FSMContext) -> None:
    """В хэндлере включается выбор канала для пробной подписки"""
    m_text = 'Выберете канал для установки пробной подписки подписки:'
    sub_keyboard = await add_sub_channel_keyboard()
    await msg.answer(text=m_text, reply_markup=sub_keyboard)
    await state.set_data({'trail': int(msg.text)})


@admin_router.callback_query(SubAddForChannel.filter(), SM.set_trail_sub)
async def end_add_trail_sub(callback: CallbackQuery, callback_data: SubAddForChannel, state: FSMContext) -> None:
    """Хэндлер завершает настройку пробной подписки"""
    trail_period = await state.get_data()
    await SubManag.trail_sub_period(period=trail_period['trail'], chn_id=int(callback_data.chn_id))
    await callback.answer()
    ans_text = (
        f'Пробная подписка <i><b>{html.quote(callback_data.chn_name)}</b></i> обновлена' if trail_period['trail'] > 0
        else f'Пробная подписка <i><b>{html.quote(callback_data.chn_name)}</b></i> отключена')
    await state.clear()
    await callback.message.answer(text=ans_text, reply_markup=sub_manag)


@admin_router.message(F.text == '➕ Добавить подписку пользователю')
async def add_sub_user(msg: Message, state: FSMContext) -> None:
    """Хэндлер запускает состояние добавления подписки пользователю в ручную"""
    await state.set_state(SM.add_subscription_a_user)
    await msg.answer(text='Введите ID пользователя или перешлите сюда любое сообщение от этого пользователя:',
                     reply_markup=cancel_button)


@admin_router.message(SM.add_subscription_a_user, F.forward_from.as_('reply') | F.text.regexp(r'\d{8,}$'))
async def add_subscription_1(msg: Message, state: FSMContext, reply=None):
    """Хэндлер добавления подписки пользователю в ручную. Активирует выбор канала."""
    if reply:
        await state.set_data({'uid': reply.id})
    else:
        await state.set_data({'uid': msg.text})
    chnl_markup = await add_sub_keyboard()
    await msg.answer(text='Выберете на какой канал хотите добавить подписку:', reply_markup=chnl_markup)


@admin_router.callback_query(AddSubForUser.filter(), SM.add_subscription_a_user)
async def add_sub_user(callback: CallbackQuery, callback_data: AddSubForUser, state: FSMContext) -> None:
    """Хэндлер добавления подписки пользователя в ручную. Ловит канал и активирует ввод периода."""
    await state.update_data({'ch_id': callback_data.chl_id})
    await state.update_data({'ch_name': callback_data.chl_name})
    await callback.message.answer(text='Введите сколько дней добавить к подписке:', reply_markup=cancel_button)


@admin_router.message(SM.add_subscription_a_user, F.text.regexp(r'\d{1,5}$'))
async def add_subscription_2(msg: Message, state: FSMContext):
    """Хэндлер завершает добавление подписки пользователю в ручную"""
    sub_info = await state.get_data()
    print(sub_info)
    await SubManag.add_user_paid_sub(
        user_id=sub_info['uid'],
        channel_id=sub_info['ch_id'],
        period=int(msg.text)
    )
    ans_text = (f'Подписка пользователю {sub_info["uid"]} на канал {sub_info["ch_name"]} '
                f'сроком на {msg.text} дня(дней) добавлена')
    await msg.answer(text=ans_text, reply_markup=sub_manag)
    await state.clear()


@admin_router.message(SM.set_trail_sub)
async def error_input_trail_sub(msg: Message) -> None:
    """Хэндлер отлавливает некорректный ввод при добавлении платного варианта подписки"""
    await msg.answer(text='Неверный ввод!\nЧисло должно быть целым и положительным', reply_markup=cancel_button)


@admin_router.message(SM.add_subscription_a_user)
async def error_input_add_sub(msg: Message) -> None:
    """Хэндлер отлавливает некорректный ввод при добавлении подписки пользователю в ручную"""
    await msg.answer(text='Неверный ввод!\nЧисло должно быть целым и положительным', reply_markup=cancel_button)


@admin_router.message(SM.set_paid_sub)
async def error_input_paid_sub(msg: Message) -> None:
    """Хэндлер отлавливает некорректный ввод при добавлении платного варианта подписки"""
    await msg.answer(text='Неверный ввод!\n'
                          'Пример: подписка на 30 дней стоимостью 100 рублей - '
                          '"30 100" без кавычек и аккуратнее с пробелами',
                     reply_markup=cancel_button)
