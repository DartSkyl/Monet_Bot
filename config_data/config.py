import os
from dotenv import load_dotenv, find_dotenv

if not find_dotenv():
    exit("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")
DB_INFO = (
    os.getenv("db_user"),
    os.getenv("db_pass"),
    os.getenv("db_name"),
    os.getenv("db_host"))

PG_URI = f"postgresql+psycopg2://{DB_INFO[0]}:{DB_INFO[1]}@{DB_INFO[3]}/{DB_INFO[2]}"

MAIN_GROUP_ID = int(os.getenv("main_group_id"))
