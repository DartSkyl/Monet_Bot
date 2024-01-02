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
            await self.connection.execute("CREATE TABLE IF NOT EXISTS all_channels"
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

            # Таблица с информацией о работе очередей публикаций
            await self.connection.execute("CREATE TABLE IF NOT EXISTS queue_info"
                                          "(channel_id BIGINT PRIMARY KEY,"
                                          "settings_info VARCHAR(155));")

            # Таблица с настройками пользовательских сообщений
            await self.connection.execute("CREATE TABLE IF NOT EXISTS users_mess"
                                          "(mess_for VARCHAR(20) PRIMARY KEY,"
                                          "mess_text TEXT)")

        except PostgresSyntaxError as exc:
            print()
            exit('Ups!\n' + str(exc))

    async def get_users_messages(self):
        """Метод выгружает сохраненные настройки пользовательских сообщений"""
        result = await self.connection.fetch("SELECT * FROM public.users_mess")
        return result

    async def set_users_messages(self, mess_for: str, mess_text: str):
        """Метод сохраняет настройки для пользовательских сообщений"""
        await self.connection.execute(f"INSERT INTO public.users_mess"
                                      f"(mess_for, mess_text)"
                                      f"VALUES ('{mess_for}', '{mess_text}')"
                                      f"ON CONFLICT (mess_for) DO UPDATE SET mess_text = '{mess_text}';")

    # ========== Методы управления каналами ==========

    async def add_channel_table(self, channel_id: int) -> None:
        """Метод добавляет таблицу для конкретного канала"""
        await self.connection.execute(f"CREATE TABLE IF NOT EXISTS channel_{abs(channel_id)}"
                                      "(user_id BIGINT PRIMARY KEY,"
                                      "end_of_subscription INT);")

    async def add_channel(self, channel_id: int, channel_name: str, paid: bool) -> None:
        """Добавление канала в общую таблицу с каналами"""
        await self.connection.execute("INSERT INTO public.all_channels"
                                      "(channel_id, channel_name, date_added, is_paid)"
                                      f"VALUES ({channel_id}, '{channel_name}', {int(time.time())}, {paid});")

    async def get_channel_list(self) -> List[Record]:
        """Получение списка имеющихся каналов из общей таблицы с каналами"""
        result = await self.connection.fetch("SELECT * FROM public.all_channels;")
        return result

    async def get_paid_channels_list(self) -> List[Record]:
        """Получение списка имеющихся закрытых каналов из общей таблицы с каналами"""
        result = await self.connection.fetch("SELECT * FROM public.all_channels WHERE is_paid = true;")
        return result

    async def delete_channel(self, channel_id: int):
        """Удаление канала из общей таблицы с каналами """
        await self.connection.execute(f"DELETE FROM public.all_channels WHERE channel_id = {channel_id};")

    async def delete_channel_table(self, channel_id: int):
        """Если канал платный, то у него есть своя таблица, которую нужно удалить, а так же
        все пробные подписки связанные с этим каналом"""
        await self.connection.execute(f"DROP TABLE public.channel_{abs(channel_id)};"
                                      f"DELETE FROM public.trail_subscription WHERE channel_id = {channel_id}")

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

    # ========== Методы управления автопостингом ==========

    async def save_queue_info(self, channel_id: int, queue_info: str) -> None:
        """Метод записывает информацию о настройках очереди публикаций"""
        await self.connection.execute("INSERT INTO public.queue_info (channel_id, settings_info)"
                                      f"VALUES ({channel_id}, '{queue_info}')"
                                      f"ON CONFLICT (channel_id) DO UPDATE SET settings_info = '{queue_info}';")

    async def get_queue_info(self, channel_id: int) -> list:
        """Метод выдает информацию о настройках очереди публикаций"""
        result = await self.connection.fetch(f"SELECT settings_info FROM public.queue_info "
                                             f"WHERE channel_id = {channel_id};")
        return result

    async def delete_jobstore_table(self, channel_id: int) -> None:
        """Метод удаляет таблицу с заданиями планировщика при удалении канала, а так же запись из таблицы queue_info"""
        await self.connection.execute(f'DROP TABLE public.aps{abs(channel_id)};'
                                      f'DELETE FROM public.queue_info WHERE channel_id = {abs(channel_id)}')

    async def create_publication_table(self, channel_id: int) -> None:
        """Метод создает таблицу с резервной копией информации для каждой публикации
        в очереди публикаций на случай сбоя"""
        await self.connection.execute(f"CREATE TABLE IF NOT EXISTS list_of_publication_{abs(channel_id)}"
                                      f"(container_id VARCHAR(10) PRIMARY KEY,"
                                      f"content_type VARCHAR(10),"
                                      f"file_id VARCHAR(100),"
                                      f"publication_text TEXT)")

    async def delete_publication_table(self, channel_id: int) -> None:
        """Метод удаляет таблицу с резервной копией списка публикаций при удалении канала"""
        await self.connection.execute(f"DROP TABLE public.list_of_publication_{abs(channel_id)}")

    async def get_list_of_publication(self, channel_id: int) -> list:
        """Метод возвращает список со всеми сохраненными публикациями"""
        result = await self.connection.fetch(f"SELECT * FROM public.list_of_publication_{abs(channel_id)}")
        return result

    async def save_publication(self, channel_id: int,
                               container_id: str,
                               content_type: str,
                               file_id: str,
                               publication_text: str) -> None:
        """Метод сохраняет публикацию в соответствующую таблицу"""
        await self.connection.execute(f"INSERT INTO public.list_of_publication_{abs(channel_id)} "
                                      f"(container_id, content_type, file_id, publication_text)"
                                      f"VALUES ('{container_id}', '{content_type}', '{file_id}', '{publication_text}');")

    async def remove_publication_from_db(self, channel_id: int, container_id: str) -> None:
        """Метод удаляет уже опубликованную публикацию"""
        await self.connection.execute(f"DELETE FROM public.list_of_publication_{abs(channel_id)} "
                                      f"WHERE container_id = '{container_id}'")
