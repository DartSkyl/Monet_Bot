from loader import channels_dict, bot, db
from utils import chat_member_router
from aiogram.types import ChatMember
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER


@chat_member_router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def new_member(chat_member: ChatMember):
    did_receive = await db.check_user_in_trail(user_id=chat_member.from_user.id, channel_id=chat_member.chat.id)
    print(did_receive)
    if chat_member.chat.id in channels_dict['free']:
        if not did_receive:
            await db.add_user_trail_subscription(user_id=chat_member.from_user.id, channel_id=chat_member.chat.id)
        else:
            print('Get out of here!')


@chat_member_router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER << IS_MEMBER))
async def new_member(chat_member: ChatMember):
    pass
