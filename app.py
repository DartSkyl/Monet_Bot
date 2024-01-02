import asyncio
import handlers  # noqa
from loader import dp, db_connect, bot, admin_list_load, channels_load, sub_settings_load
from utils import admin_router, chat_member_router, users_router, create_publish_queue
from utils.subscription_management import check_subscription


async def start_up():
    #  Подключаем свои роутеры
    dp.include_router(admin_router)
    dp.include_router(chat_member_router)
    dp.include_router(users_router)
    #  Подключаемся к базе
    await db_connect()
    #  Загружаем ID администраторов прямо из основной группы
    await admin_list_load()
    # Загружаем ID каналов из БД в оперативную память, если такие имеются
    await channels_load()
    # Загружаем варианты подписок
    await sub_settings_load()
    #  Пропускаем скопившиеся апдэйты
    await bot.delete_webhook(drop_pending_updates=True)
    await check_subscription()
    await create_publish_queue()
    # Стартуем! Я начну стрелять!
    print('Bot is work!')
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(start_up())
    except KeyboardInterrupt:
        print('Bot stopped')
