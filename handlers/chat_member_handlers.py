from loader import channels_dict, bot, db
from utils import chat_member_router, SubManag
from aiogram.types import ChatMember
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER


@chat_member_router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def new_member(chat_member: ChatMember):
    if chat_member.chat.id in channels_dict['is_paid']:
        # Проверяем выдавалась ли пробная подписка пользователю в этом канале
        did_receive = await db.check_user_in_trail(user_id=chat_member.from_user.id, channel_id=chat_member.chat.id)
        print(did_receive)
        if not did_receive:
            await SubManag.add_user_trail_sub(user_id=chat_member.from_user.id, channel_id=chat_member.chat.id)

        else:
            print('Get out of here!')


@chat_member_router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER << IS_MEMBER))
async def new_member(chat_member: ChatMember):
    pass
