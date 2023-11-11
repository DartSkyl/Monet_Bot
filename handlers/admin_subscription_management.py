import time
from asyncio import sleep
from loader import bot, channels_dict, subscription_dict, db
from utils import admin_router, SubManag
from states import SubscriptionManagement as SM
from kyeboards import cancel_button, main_admin_keyboard, sub_manag, del_board, SubDel, add_sub_keyboard, AddSubForUser
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram import F


@admin_router.message(F.text == '2')
async def test2(msg):
    a = await db.get_user_from_channel(user_id=693157146, channel_id=-1001972569166)
    print(a[0])


@admin_router.message(F.text == '⚙️ Посмотреть/удалить установленные подписки')
async def check_sub_settings(msg: Message) -> None:
    """Хэндлер выводит актуальную информацию по подпискам"""
    tr_sub = await SubManag.get_trail_period()
    ans_text = (f'Пробная подписка: {tr_sub} дня(дней)' if tr_sub > 0
                else 'Пробная подписка отключена')
    for period, cost in sorted(subscription_dict.items()):
        if period != '0':  # Так как под этим ключом хранится пробный период
            ans_text += f'\n{period} дней, стоимость {str(cost)}'
    if len(subscription_dict) == 1:  # На случай, если платных подписок нет, а в словаре только один пробный период
        ans_text += '\nПлатных подписок нет!'
    await msg.answer(text=ans_text,
                     reply_markup=del_board())


@admin_router.message(F.text == '💵 Добавить платную подписку')
async def set_paid_subscription(msg: Message, state: FSMContext) -> None:
    m_text = ('Введите желаемый срок подписки и стоимость через пробел\n'
              'Пример: подписка на 30 дней стоимостью 100 рублей - "30 100" без кавычек')
    await msg.answer(text=m_text, reply_markup=cancel_button)
    await state.set_state(SM.set_paid_sub)


@admin_router.message(F.text == '⏲️ Изменить период пробной подписки')
async def set_trail_subscription(msg: Message, state: FSMContext) -> None:
    """Хэндлер запускает состояние изменения пробной подписки"""
    await state.set_state(SM.set_trail_sub)
    await msg.answer(text="Введите количество дней для пробной подписки\n"
                          "Что бы отключить пробную подписку введите 0", reply_markup=cancel_button)


@admin_router.message(F.text == '➕ Добавить подписку пользователю')
async def add_sub_user(msg: Message, state: FSMContext) -> None:
    """Хэндлер запускает состояние добавления подписки пользователю в ручную"""
    await state.set_state(SM.add_subscription_a_user)
    await msg.answer(text='Введите ID пользователя или перешлите сюда любое сообщение от этого пользователя:',
                     reply_markup=cancel_button)


@admin_router.message(SM.add_subscription_a_user, F.forward_from.as_('reply') | F.text.regexp(r'\d{8,}$'))
async def add_subscription_1(msg: Message, state: FSMContext, reply=None):
    if reply:
        await state.set_data({'uid': reply.id})
    else:
        await state.set_data({'uid': msg.text})
    chnl_markup = await add_sub_keyboard()
    await msg.answer(text='Выберете на какой канал хотите добавить подписку:', reply_markup=chnl_markup)


@admin_router.callback_query(AddSubForUser.filter(), SM.add_subscription_a_user)
async def add_sub_user(callback: CallbackQuery, callback_data: AddSubForUser, state: FSMContext) -> None:
    await state.update_data({'ch_id': callback_data.chl_id})
    await state.update_data({'ch_name': callback_data.chl_name})
    await callback.message.answer(text='Введите сколько дней добавить к подписке:', reply_markup=cancel_button)


@admin_router.message(SM.add_subscription_a_user, F.text.regexp(r'\d{1,5}$'))
async def add_subscription_2(msg: Message, state: FSMContext):
    sub_info = await state.get_data()
    print(sub_info)
    await SubManag.add_user_paid_sub(
        user_id=sub_info['uid'],
        channel_id=sub_info['ch_id'],
        period=int(msg.text)
    )
    ans_text = (f'Подписка пользователю {sub_info["uid"]} на канал {sub_info["ch_name"]} '
                f'сроком на {msg.text} дня(дней) добавлена')
    await state.clear()
    await msg.answer(text=ans_text, reply_markup=sub_manag)


@admin_router.message(SM.set_paid_sub, F.text.regexp(r'\d{1,}\s\d{1,}$'))
async def set_paid_sub(msg: Message, state: FSMContext) -> None:
    sub_set = msg.text.split()
    if int(sub_set[0]) > 0:
        await SubManag.set_paid_subscription(sub_set[0], int(sub_set[1]))
        ans_text = f'Подписка на {sub_set[0]} дней стоимостью {sub_set[1]} добавлена!'
        await msg.answer(text=ans_text, reply_markup=sub_manag)
        await state.clear()
    else:
        await msg.answer(text='Подписка на 0 дней? Давай еще раз попробуем!', reply_markup=cancel_button)


@admin_router.message(SM.set_trail_sub, F.text.regexp(r'\d{1,}'))
async def set_trail_subscription_period(msg: Message, state: FSMContext) -> None:
    """В хэндлере происходит установка пробной подписки"""
    await SubManag.trail_sub_period(int(msg.text))
    await msg.answer(text=f'Период пробной подписки установлен на {msg.text} дней' if int(msg.text) > 0
                          else 'Пробная подписка отключена',
                     reply_markup=sub_manag)
    await state.clear()


@admin_router.callback_query(SubDel.filter())
async def sub_delete(callback: CallbackQuery, callback_data: SubDel) -> None:
    await SubManag.delete_subscription(callback_data.sub_info)
    await callback.answer(text=f'Подписка на {callback_data.sub_info} дней удалена')
    tr_sub = await SubManag.get_trail_period()
    ans_text = (f'Пробная подписка: {tr_sub} дня(дней)' if tr_sub > 0
                else 'Пробная подписка отключена')
    for period, cost in sorted(subscription_dict.items()):
        if period != '0':  # Так как под этим ключом хранится пробный период
            ans_text += f'\n{period} дней, стоимость {str(cost)}'
    await callback.message.edit_text(text=ans_text)
    try:
        await callback.message.edit_reply_markup(reply_markup=del_board())
    except TelegramBadRequest as exc:  # Выскочит, если нет вариантов для создания клавиатуры
        await callback.message.edit_text(text=ans_text + '\nПлатных подписок нет!')
        print('Нет вариантов для создания клавиатуры!\n', exc)


@admin_router.message(SM.set_trail_sub)
async def error_input_trail_sub(msg: Message) -> None:
    await msg.answer(text='Неверный ввод!\nЧисло должно быть целым и положительным', reply_markup=cancel_button)


@admin_router.message(SM.add_subscription_a_user)
async def error_input_add_sub(msg: Message) -> None:
    await msg.answer(text='Неверный ввод!\nЧисло должно быть целым и положительным', reply_markup=cancel_button)


@admin_router.message(SM.set_paid_sub)
async def error_input_paid_sub(msg: Message) -> None:
    await msg.answer(text='Неверный ввод!\n'
                     'Пример: подписка на 30 дней стоимостью 100 рублей - '
                     '"30 100" без кавычек и аккуратнее с пробелами',
                     reply_markup=cancel_button)

# @admin_router.message(Command("ban"))
# async  def handing_message(msg):
#     await bot.ban_chat_member(chat_id=-1001513097504, user_id=6724839493)
#
#
# @admin_router.message(Command("unban"))
# async  def handing_message(msg):
#     await bot.unban_chat_member(chat_id=-1001513097504, user_id=6724839493)
