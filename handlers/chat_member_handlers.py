import time
from datetime import date
from config import MAIN_GROUP_ID
from loader import channels_dict, bot, db, subscription_dict, users_mess_dict, admins_id
from utils import chat_member_router, SubManag
from aiogram import F, html
from aiogram.types import ChatMember
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, ADMINISTRATOR, MEMBER


@chat_member_router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> MEMBER))
async def new_member(chat_member: ChatMember):
    """Хэндлер ловит нового подписчика любого из каналов.
    Если канал открытый, то просто добавляем его в статистику канала.
    Если канала платный, то сначала проверяем наличие подписки. При отсутствии подписки смотрим
    есть ли у канала пробная. Если есть, то пропускаем пользователя дальше с начислением ему пробной подписки и
    соответствующим сообщением.
    Если пробной подписки на канале нет или он ее уже получал, то кикаем пользователя с баном на одну минуту
    и сообщаем ему, что нужно оплатить подписку"""
    if chat_member.chat.id in channels_dict['is_paid']:
        # Запись о пользователе из таблицы канала удаляется только когда заканчивается подписка.
        # И появляется как только он оплатил подписку или выдалась пробная подписка

        # Здесь мы получаем список с записями конкретного пользователя из таблицы канала куда он подписался.
        # Если список пуст, значит подписки у пользователя нет
        usr = await db.get_user_from_channel(user_id=chat_member.from_user.id, channel_id=chat_member.chat.id)
        channel_name = (await bot.get_chat(chat_member.chat.id)).title
        msg_prefix = html.quote(f'{channel_name}\n===========\n\n')
        if len(usr) == 0:

            if subscription_dict[chat_member.chat.id][0] > 0:  # Проверяем, включена ли вообще пробная подписка

                # Проверяем выдавалась ли пробная подписка пользователю в этом канале
                did_receive = await db.check_user_in_trail(user_id=chat_member.from_user.id,
                                                           channel_id=chat_member.chat.id)
                if not did_receive:
                    await bot.unban_chat_member(chat_id=chat_member.chat.id, user_id=chat_member.from_user.id)
                    await SubManag.add_user_trail_sub(user_id=chat_member.from_user.id, channel_id=chat_member.chat.id)
                    await bot.send_message(chat_id=chat_member.from_user.id,
                                           text=(msg_prefix + users_mess_dict['trail_sub']))
                    # Метод сразу фиксирует и подписчика, и пробную подписку
                    await db.count_trail_subscription(channel_id=chat_member.chat.id, date_today=str(date.today()))

                else:  # Если пробная подписка уже выдавалась
                    await bot.ban_chat_member(user_id=chat_member.from_user.id, chat_id=chat_member.chat.id)
                    await bot.send_message(chat_id=chat_member.from_user.id,
                                           text=(msg_prefix + users_mess_dict['was_trail']))

            else:  # Если пробная подписка отключена, а платную еще не подключил
                await bot.ban_chat_member(user_id=chat_member.from_user.id, chat_id=chat_member.chat.id)
                await bot.send_message(chat_id=chat_member.from_user.id,
                                       text=(msg_prefix + users_mess_dict['not_trail']))

        else:  # Если подписка уже есть, то просто заносим в статистику
            await db.new_member(channel_id=chat_member.chat.id, date_today=str(date.today()))

    else:  # Если канал открытый
        await db.new_member(channel_id=chat_member.chat.id, date_today=str(date.today()))


@chat_member_router.chat_member(F.chat.id.in_(channels_dict['free']),
                                ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER << MEMBER))
async def out_of_channel(chat_member: ChatMember):
    """Хэндлер ловит тех, кто отписывается от открытого канала"""

    await db.count_out_of_channel(channel_id=chat_member.chat.id, date_today=str(date.today()))

    # Если канал платный тут несколько вариантов:
    # 1) Закончилась подписка - бот банит
    # 2) При попытке подписаться с отключенной у канала пробной подпиской (или уже выдавалась) - бот банит
    # 3) Подписчик сам отписался, но подписка еще осталась - здесь считать не будем,
    # так как при окончании подписки бот его отминусует. В первых двух случаях счетчик уже стоит


@chat_member_router.chat_member(F.chat.id == MAIN_GROUP_ID,
                                ChatMemberUpdatedFilter(
                                    member_status_changed=(MEMBER | IS_NOT_MEMBER) >> ADMINISTRATOR)
                                )
async def new_administrator(chat_member: ChatMember):
    """Ловим новых администраторов бота только из основной группы"""
    admins_id.append(chat_member.new_chat_member.user.id)


@chat_member_router.chat_member(F.chat.id == MAIN_GROUP_ID,
                                ChatMemberUpdatedFilter(
                                    member_status_changed=(MEMBER | IS_NOT_MEMBER) << ADMINISTRATOR)
                                )
async def remove_administrator(chat_member: ChatMember):
    """Удаляем администратора из списка с ID администраторов"""
    admins_id.remove(chat_member.new_chat_member.user.id)
