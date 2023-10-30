import asyncio
from loader import dp, db_connect, bot, admin_list_load
from utils import admin_router, chat_member_router, users_router
import handlers  # noqa


async def start_up():

    #  Подключаем свои роутеры
    dp.include_router(admin_router)
    dp.include_router(chat_member_router)
    dp.include_router(users_router)

    #  Подключаемся к базе
    await db_connect()

    #  Загружаем ID администраторов прямо из основной группы
    await admin_list_load()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(start_up())
    except KeyboardInterrupt:
        print('Bot stopped')
