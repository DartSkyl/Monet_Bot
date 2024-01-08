import time
from config_data.config import MAIN_GROUP_ID
from loader import channels_dict, bot, db, subscription_dict, users_mess_dict, admins_id
from utils import chat_member_router, SubManag
from aiogram import F
from aiogram.types import ChatMember
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, ADMINISTRATOR, MEMBER


@chat_member_router.chat_member(F.chat.id.in_([channels_dict['is_paid']]),
                                ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> MEMBER))
async def new_member(chat_member: ChatMember):
    # На всякий случай проверим, может у пользователя уже есть подписка (он мог случайно выйти из группы или еще что)
    # Запись о пользователе из таблицы канала удаляется только когда заканчивается подписка
    usr = await db.get_user_from_channel(user_id=chat_member.from_user.id, channel_id=chat_member.chat.id)
    if len(usr) == 0:
        if subscription_dict[chat_member.chat.id][0] > 0:  # Проверяем, включена ли вообще пробная подписка
            # Проверяем выдавалась ли пробная подписка пользователю в этом канале
            did_receive = await db.check_user_in_trail(user_id=chat_member.from_user.id, channel_id=chat_member.chat.id)
            if not did_receive:
                await SubManag.add_user_trail_sub(user_id=chat_member.from_user.id, channel_id=chat_member.chat.id)
                await bot.send_message(chat_id=chat_member.from_user.id,
                                       text=users_mess_dict['trail_sub'])
            else:
                await bot.ban_chat_member(user_id=chat_member.from_user.id, chat_id=chat_member.chat.id,
                                          until_date=(int(time.time()) + 60))
                await bot.send_message(chat_id=chat_member.from_user.id,
                                       text=users_mess_dict['was_trail'])
        else:
            await bot.ban_chat_member(user_id=chat_member.from_user.id, chat_id=chat_member.chat.id,
                                      until_date=(int(time.time()) + 60))
            await bot.send_message(chat_id=chat_member.from_user.id,
                                   text=users_mess_dict['not_trail'])


@chat_member_router.chat_member(F.chat.id == MAIN_GROUP_ID,
                                ChatMemberUpdatedFilter(
                                    member_status_changed=(MEMBER | IS_NOT_MEMBER) >> ADMINISTRATOR),
                                )
async def new_administrator(chat_member: ChatMember):
    """Ловим новых администраторов бота только из основной группы"""
    admins_id.append(chat_member.new_chat_member.user.id)


@chat_member_router.chat_member(F.chat.id == MAIN_GROUP_ID,
                                ChatMemberUpdatedFilter(
                                    member_status_changed=(MEMBER | IS_NOT_MEMBER) << ADMINISTRATOR),
                                )
async def remove_administrator(chat_member: ChatMember):
    """Удаляем администратора из списка с ID администраторов"""
    admins_id.remove(chat_member.new_chat_member.user.id)
