import os
from dotenv import load_dotenv, find_dotenv

if not find_dotenv():
    exit("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_INFO = (
    os.getenv("db_user"),
    os.getenv("db_pass"),
    os.getenv("db_name"),
    os.getenv("db_port"))
