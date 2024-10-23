import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.requests import Request
import uvicorn
from aiogram.types import Update

import handlers  # noqa
from loader import dp, db_connect, bot, admin_list_load, channels_load, sub_settings_load, load_user_messages
from utils import admin_router, chat_member_router, users_router, create_publish_queue
from utils.subscription_management import check_subscription
from config import WEBHOOK


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa
    await bot.delete_my_commands()
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
    url_webhook = WEBHOOK
    await bot.set_webhook(url=url_webhook,
                          allowed_updates=dp.resolve_used_update_types(),
                          drop_pending_updates=True)
    yield
    await bot.delete_webhook()


app = FastAPI(lifespan=lifespan)


@app.post("/webhook/monet_bot")
async def webhook(request: Request) -> None:
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)


if __name__ == '__main__':
    try:
        # asyncio.run(start_up())
        uvicorn.run(app, host="0.0.0.0", port=5000)
    except KeyboardInterrupt:
        print('Хорош, бро')
