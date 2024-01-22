from datetime import date, datetime
from config_data.config import PAYMENT_TOKEN
from loader import users_mess_dict, bot, db, subscription_dict, admins_id
from states import UserPayment, CommunicationAdministration
from utils import users_router
from utils.subscription_management import SubManag
from keyboards import (main_user_keyboard, channels_selection,
                       view_description, ChannelsSelection,
                       subscription_keyboard, SubscriptionSelection,
                       ChannelsForPayment, channels_for_payment, user_cancel)
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram import F, html
from aiogram.filters import Command
from aiogram.exceptions import TelegramForbiddenError


@users_router.message(Command('start'))
async def user_start(msg: Message) -> None:
    """Здесь начинается взаимодействие с пользователем"""
    await msg.answer(text=users_mess_dict['hi_mess'],
                     reply_markup=main_user_keyboard)


@users_router.message(F.text == '🔎 Посмотреть доступные каналы')
async def looking_channels(msg: Message):
    """Здесь выводим список доступных каналов. И платных, и нет"""
    msg_text = '⬇️<b>Выберете один из каналов ниже для просмотра</b>⬇️'
    await msg.answer(text=msg_text, reply_markup=await channels_selection())


@users_router.callback_query(ChannelsSelection.filter())
async def view_description_and_go_to_channel(callback: CallbackQuery, callback_data: ChannelsSelection):
    """Здесь показываем описание и предлагаем перейти в канал или вернуться назад к списку каналов"""
    channel = await bot.get_chat(callback_data.channel_id)
    channel_url = channel.invite_link  # Ссылка на канал
    channel_name = channel.title

    msg_text = f'Описание канала <i><b>{html.quote(channel_name)}</b></i>:\n'
    msg_text += '<i>- Отсутствует -</i>' if not users_mess_dict.get(str(callback_data.channel_id)) \
        else html.quote(users_mess_dict[str(callback_data.channel_id)])

    await callback.message.delete()
    await callback.message.answer(text=msg_text, reply_markup=await view_description(channel_url))


@users_router.callback_query(F.data.in_(['go_back', 'cancel']))
async def return_and_cancel(callback: CallbackQuery):
    """Здесь возврат и отмена"""
    if callback.data == 'go_back':
        await callback.message.delete()
        msg_text = '⬇️<b>Выберете один из каналов ниже для просмотра</b>⬇️'
        await callback.message.answer(text=msg_text, reply_markup=await channels_selection())
    else:
        await callback.message.delete()
        await callback.message.answer(text='Отмена действия', reply_markup=main_user_keyboard)


@users_router.message(F.text == 'ℹ️ Информация о Вашей подписке')
async def get_subscription_info(msg: Message):
    """Здесь выводится информация о всех имеющихся подписках"""
    paid_channels = await db.get_paid_channels_list()
    user_id = msg.from_user.id
    msg_text = '<b>Ваши действующие подписки</b>\n====================\n'
    for channel in paid_channels:  # Пройдемся по всем платным каналам
        user_subscription = await db.get_user_from_channel(user_id=user_id, channel_id=channel['channel_id'])
        if len(user_subscription) > 0:  # Если в списке по этому каналу записей у подписчика нет, значит и подписки тоже
            end_sub = datetime.fromtimestamp(user_subscription[0]['end_of_subscription']).strftime('%m-%d-%Y %H:%M')
            msg_text += f'<i><b>{html.quote(channel["channel_name"])}</b></i> - действует до <i>{end_sub}</i>\n\n'

    await msg.answer(text=msg_text)


@users_router.message(F.text == '💳 Оплатить подписку')
async def start_pay_for_subscription(msg: Message, state: FSMContext):
    """Здесь запускаем формирование оплаты за подписку"""
    await state.set_state(UserPayment.choice_channel)
    await msg.answer(text='Выберете канал:', reply_markup=await channels_for_payment())


@users_router.callback_query(UserPayment.choice_channel, ChannelsForPayment.filter())
async def select_subscription(callback: CallbackQuery, callback_data: ChannelsForPayment, state: FSMContext):
    """После выбора канал даем на выбор варианты подписок данного канала"""
    # Сразу сохраним выбор пользователя
    channel_name = (await bot.get_chat(callback_data.channel_id)).title
    await state.set_data({'channel_id': callback_data.channel_id, 'channel_name': channel_name})
    await callback.message.delete()
    msg_text = f'Канал: <b>{html.quote(channel_name)}</b>\nВыберете вариант подписки:'
    await callback.message.answer(text=msg_text,
                                  reply_markup=await subscription_keyboard(subscription_dict[callback_data.channel_id]))
    await state.set_state(UserPayment.choice_period)


@users_router.callback_query(UserPayment.choice_period, SubscriptionSelection.filter())
async def formation_of_payment(callback: CallbackQuery, callback_data: SubscriptionSelection, state: FSMContext):
    """Здесь формируем счет для оплаты"""
    sub_info = await state.get_data()
    des_text = (f'Приобретение подписки на канал {sub_info["channel_name"]} '
                f'сроком на {callback_data.period} дня/дней')
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f'Канал {sub_info["channel_name"]}',
        description=des_text,
        payload=f'{sub_info["channel_id"]}_{callback_data.cost}',
        provider_token=PAYMENT_TOKEN,
        currency='rub',
        prices=[LabeledPrice(
            label=f'Подписка на {callback_data.period} дня/дней',
            amount=(callback_data.cost * 100))],
        start_parameter='Go',
        request_timeout=15)
    await state.update_data({'period': callback_data.period, 'cost': callback_data.cost})
    await state.set_state(UserPayment.payment)  # На всякий случай зададим стэйт


@users_router.pre_checkout_query(UserPayment.payment)
async def pre_check_query(pre_check: PreCheckoutQuery):
    """Говорим телеграмму, что все ОК"""
    await pre_check.answer(ok=True)


@users_router.message(UserPayment.payment, F.successful_payment)
async def test_payment(msg: Message, state: FSMContext):
    """Когда оплата подтвердится начисляем подписку пользователю согласно заявленным параметрам"""
    sub_info = await state.get_data()

    # Накидываем подписку через соответствующий метод

    await SubManag.add_user_paid_sub(
        user_id=msg.from_user.id,
        channel_id=sub_info['channel_id'],
        period=sub_info['period']
    )

    # Отправляем в бухгалтерию
    await db.add_revenue(
        channel_id=sub_info['channel_id'],
        date_today=str(date.today()),
        revenue=int(sub_info['cost'])
    )

    msg_text = (f'Подписка для канала <i><b>{html.quote(sub_info["channel_name"])}</b></i>\n'
                f'сроком на <b>{sub_info["period"]}</b> дня/дней\n'
                f'добавлена!\n')
    msg_text += users_mess_dict['paid']
    await msg.answer(text=msg_text, reply_markup=main_user_keyboard)
    await state.clear()


@users_router.message(F.text == '📨 Связаться с администрацией')
async def communication_with_the_administration(msg: Message, state: FSMContext):
    """Здесь происходит связь с администрацией"""
    # Если юзернэйм для связи с подписчиками установлен
    if users_mess_dict['admin_username'] and users_mess_dict['admin_username'] != '@__None__':
        await msg.answer(text=f'Контакт для связи: {users_mess_dict["admin_username"]}')

    else:
        await msg.answer(text='Введите текст сообщения:', reply_markup=user_cancel)
        await state.set_state(CommunicationAdministration.write_message)


@users_router.message(F.text == '🚫 Отмена')
async def send_message_cancel(msg: Message, state: FSMContext):
    """Отмена отправки сообщения"""
    await msg.answer(text='Действие отменено', reply_markup=main_user_keyboard)
    await state.clear()


@users_router.message(CommunicationAdministration.write_message)
async def send_user_message(msg: Message, state: FSMContext):
    """Если юзернэйм администратора для связи с подписчиками не установлен
    рассылаем сообщение пользователя по всем админам"""
    for admin in admins_id:
        try:
            await msg.forward(chat_id=admin)
        except TelegramForbiddenError:
            # В списке ID администраторов будет и ID самого бота.
            # И при попытке отправить сообщение самому себе выскочит это исключение
            pass

    await msg.answer(text='Сообщение отправлено!', reply_markup=main_user_keyboard)
    await state.clear()
