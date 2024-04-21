import asyncio
import datetime
import handlers  # noqa
from loader import dp, db_connect, bot, admin_list_load, channels_load, sub_settings_load, load_user_messages
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
    # Загружаем пользовательские сообщения
    await load_user_messages()
    # Запускаем проверку подписок
    await check_subscription()
    # Создаем очереди публикаций
    await create_publish_queue()
    # Стартуем! Я начну стрелять!
    with open('bot.log', 'a') as log_file:
        log_file.write(f'\n========== New bot session {datetime.datetime.now()} ==========\n\n')
    print('Стартуем')
    await dp.start_polling(bot,
                           allowed_updates=[
                               "message",
                               "callback_query",
                               "pre_checkout_query",
                               "chat_member"
                           ])


if __name__ == '__main__':
    try:
        asyncio.run(start_up())
    except KeyboardInterrupt:
        print('Хорош, бро')
