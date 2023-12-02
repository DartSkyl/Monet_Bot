import time
from typing import List
import asyncpg as apg
from asyncpg import Record
from asyncpg.exceptions import PostgresSyntaxError


class BotBase:
    """Через данный класс реализованы конект с базой данных и методы взаимодействия с БД"""

    def __init__(self, _db_user, _db_pass, _db_name, _db_host):
        self.db_name = _db_name
        self.db_user = _db_user
        self.db_pass = _db_pass
        self.db_host = _db_host
        self.connection = None

    async def connect(self) -> None:
        """Метод создания соединения с базой"""
        self.connection = await apg.connect(database=self.db_name, user=self.db_user, password=self.db_pass,
                                            host=self.db_host)

    async def check_db_structure(self) -> None:
        try:

            # Таблица со всеми группами
            await self.connection.execute("CREATE TABLE IF NOT EXISTS groups"
                                          "(channel_id BIGINT PRIMARY KEY,"
                                          "channel_name VARCHAR(130),"
                                          "date_added INT,"
                                          "is_paid BOOLEAN);")

            # Таблица с юзерами, которым была выдана пробная подписка
            await self.connection.execute("CREATE TABLE IF NOT EXISTS trail_subscription"
                                          "(user_id BIGINT,"
                                          "channel_id BIGINT,"
                                          "data_activate INT);")

            # Таблица с настройками подписок. Что бы при перезапуске бота не настраивать заново
            await self.connection.execute("CREATE TABLE IF NOT EXISTS sub_settings"
                                          # Строка будет хранить сразу и период подписки и ID канала для этого варианта
                                          "(chl_id_period VARCHAR(100) PRIMARY KEY ," 
                                          "cost INT);")

        except PostgresSyntaxError as exc:
            print()
            exit('Ups!\n' + str(exc))

    # ========== Методы управления каналами ==========

    async def add_channel_table(self, channel_id: int) -> None:
        """Метод добавляет таблицу для конкретного канала"""
        await self.connection.execute(f"CREATE TABLE IF NOT EXISTS channel_{abs(channel_id)}"
                                      "(user_id BIGINT PRIMARY KEY,"
                                      "end_of_subscription INT);")

    async def add_channel(self, channel_id: int, channel_name: str, paid: bool) -> None:
        """Добавление канала в общую таблицу с каналами"""
        await self.connection.execute("INSERT INTO public.groups"
                                      "(channel_id, channel_name, date_added, is_paid)"
                                      f"VALUES ({channel_id}, '{channel_name}', {int(time.time())}, {paid});")

    async def get_channel_list(self) -> List[Record]:
        """Получение списка имеющихся каналов из общей таблицы с каналами"""
        result = await self.connection.fetch("SELECT * FROM public.groups;")
        return result

    async def get_paid_channels_list(self) -> List[Record]:
        """Получение списка имеющихся закрытых каналов из общей таблицы с каналами"""
        result = await self.connection.fetch("SELECT * FROM public.groups WHERE is_paid = true;")
        return result

    async def delete_channel(self, channel_id: int):
        """Удаление канала из общей таблицы с каналами"""
        await self.connection.execute(f"DELETE FROM public.groups WHERE channel_id = {channel_id};")

    # ========== Методы управления подписками ==========

    async def add_user_trail_subscription(self, user_id: int, channel_id: int) -> None:
        """Добавляет в БД пользователя, которому была выдана пробная подписка на конкретный канал.
        Уникальных ключей в таблице нет."""

        await self.connection.execute("INSERT INTO public.trail_subscription"
                                      "(user_id, channel_id, data_activate)"
                                      f"VALUES ({user_id}, {channel_id}, {int(time.time())});")

    async def check_user_in_trail(self, user_id: int, channel_id: int) -> bool:
        """Данный метод проверяет, есть такое сочетание ID пользователя и ID канала,
        так как один пользователь может получить пробную подписку в разных каналах"""

        result = await self.connection.fetch(f"SELECT * FROM public.trail_subscription "
                                             f"WHERE user_id = {user_id} AND channel_id = {channel_id};")

        return len(result) > 0  # Если пользователь уже получал пробную подписку в этом канале, то вернется True

    async def add_user_in_paid_channel(self, user_id: int, channel_id: int, subscription: int) -> None:
        """Метод добавляет пользователя в таблицу закрытого канала"""
        await self.connection.execute(f"INSERT INTO public.channel_{abs(channel_id)}"
                                      "(user_id, end_of_subscription)"
                                      f"VALUES ({user_id}, {time.time() + subscription});")

    async def list_of_user_subscriptions(self, channel_id) -> List[Record]:
        """Метод выдает список подписок пользователей для дальнейшей проверки"""
        result = await self.connection.fetch(f"SELECT * FROM public.channel_{abs(channel_id)};")
        return result

    async def set_sub_setting(self, chl_id_period: str, cost: int) -> None:
        """Метод записывает в базу настройки для вариантов подписки"""
        await self.connection.execute(f"INSERT INTO public.sub_settings (chl_id_period, cost)"
                                      f"VALUES ('{chl_id_period}', {cost})"
                                      f"ON CONFLICT (chl_id_period) DO UPDATE SET cost = {cost};")

    async def get_sub_setting(self) -> List[Record]:
        """Метод получения из БД вариантов подписки"""
        result = await self.connection.fetch("SELECT * FROM public.sub_settings;")
        return result

    async def delete_subscription(self, chl_id_period: str) -> None:
        """Метод удаляет вариант подписки из базы"""
        await self.connection.execute(f"DELETE FROM public.sub_settings WHERE chl_id_period = '{chl_id_period}';")

    async def get_user_from_channel(self, user_id, channel_id) -> List[Record]:
        """Метод получения пользователя из таблицы конкретного канала"""
        result = await self.connection.fetch(f"SELECT * FROM public.channel_{abs(channel_id)} "
                                             f"WHERE user_id = {user_id};")
        return result

    async def subscription_update(self, user_id: int, channel_id: int, new_sub: int) -> None:
        """Метод обновляет подписку пользователя в конкретном канале"""
        await self.connection.execute(f"UPDATE public.channel_{abs(channel_id)} "
                                      f"SET end_of_subscription = {new_sub} "
                                      f"WHERE user_id = {user_id};")

    async def delete_user_from_channel(self, user_id: int, channel_id: int) -> None:
        """Метод удаления пользователя из таблицы конкретного канала"""
        await self.connection.execute(f"DELETE FROM public.channel_{abs(channel_id)} WHERE user_id = {user_id}")
