from loader import dp
import handlers  # noqa
from aiogram import executor


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp)
