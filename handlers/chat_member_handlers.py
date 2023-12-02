import time
from loader import channels_dict, bot, db, subscription_dict
from utils import chat_member_router, SubManag
from aiogram.types import ChatMember
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER


@chat_member_router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def new_member(chat_member: ChatMember):
    # На всякий случай проверим, может у пользователя уже есть подписка (он мог случайно выйти из группы или еще что)
    # Запись о пользователе из таблицы канала удаляется только когда заканчивается подписка
    usr = await db.get_user_from_channel(user_id=chat_member.from_user.id, channel_id=chat_member.chat.id)
    if len(usr) == 0:
        if subscription_dict[chat_member.chat.id]['0'] > 0:  # Проверяем, включена ли вообще пробная подписка
            # Проверяем выдавалась ли пробная подписка пользователю в этом канале
            did_receive = await db.check_user_in_trail(user_id=chat_member.from_user.id, channel_id=chat_member.chat.id)
            print(did_receive)
            if not did_receive:
                await SubManag.add_user_trail_sub(user_id=chat_member.from_user.id, channel_id=chat_member.chat.id)
            else:
                await bot.ban_chat_member(user_id=chat_member.from_user.id, chat_id=chat_member.chat.id,
                                          until_date=(int(time.time()) + 31))
                await bot.send_message(chat_id=chat_member.from_user.id,
                                       text="Пробная подписка вам уже выдавалась! Пожалуйста, оплатите подписку!")
        else:
            await bot.ban_chat_member(user_id=chat_member.from_user.id, chat_id=chat_member.chat.id,
                                      until_date=(int(time.time()) + 31))
            await bot.send_message(chat_id=chat_member.from_user.id,
                                   text="Что бы получить доступ к каналу, нужно оплатить подписку!")


@chat_member_router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER << IS_MEMBER))
async def new_member(chat_member: ChatMember):
    pass
