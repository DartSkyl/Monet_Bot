from utils import chat_member_router
from aiogram.types import ChatMember
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER


@chat_member_router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def new_member(chat_member: ChatMember):
    print("\nNew member!")
    print("From user id:", chat_member.from_user.id)
    print("Chat id:", chat_member.chat.id, '\n')


@chat_member_router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER << IS_MEMBER))
async def new_member(chat_member: ChatMember):
    print("\nMember left!")
    print("From user id:", chat_member.from_user.id)
    print("Chat id:", chat_member.chat.id, '\n')
