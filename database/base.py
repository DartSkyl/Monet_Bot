import asyncpg as apg
from asyncpg.exceptions import PostgresSyntaxError


class BotBase:
    """Через данный класс реализованы конект с базой данных и методы создания таблиц"""
    def __init__(self,_db_user,  _db_pass, _db_name, _db_host):
        self.db_name = _db_name
        self.db_user = _db_user
        self.db_pass = _db_pass
        self.db_host = _db_host
        self.connection = None

    async def connect(self):
        """Метод создания конекта с базой"""
        self.connection = await apg.connect(database=self.db_name, user=self.db_user, password=self.db_pass,
                                            host=self.db_host)

    async def check_db_structure(self):
        try:  # Таблица со всеми группами
            await self.connection.execute("CREATE TABLE IF NOT EXISTS groups"
                                          "(group_id BIGINT PRIMARY KEY,"
                                          "group_name VARCHAR(130),"
                                          "date_added FLOAT,"
                                          "is_close BOOLEAN);")

            # Таблица с юзерами, которым была выдана пробная подписка
            await self.connection.execute("CREATE TABLE IF NOT EXISTS trail_subscription"
                                          "(user_id BIGINT PRIMARY KEY,"
                                          "data_activate FLOAT)")
        except PostgresSyntaxError as exc:
            print('Ups!\n', exc)
            exit()
