from aiogram import Bot, Dispatcher
from config_data.config import BOT_TOKEN


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot=bot)
