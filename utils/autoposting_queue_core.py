import time

from aiogram.utils.media_group import MediaGroupBuilder

from config_data.config import PG_URI
from loader import db, bot, admins_id
from .autoposting_content_container import ContentContainer

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import html
from aiogram.exceptions import TelegramForbiddenError


dict_queue = dict()


async def publish_post(channel_id: int):
    """Данная функция отвечает за публикацию постов в каналах, привязанных к боту.
    На входе получает только ID канала"""
    try:
        queue = dict_queue[-channel_id]
        publication = (await queue.get_list_publication())[0]
        publication_file_id = publication.get_file_id()

        if publication_file_id:  # Если данный список пуст, значит объявление без медиафайлов
            media_group = MediaGroupBuilder(caption=publication.get_text())
            for mediafile in publication_file_id:
                media_group.add(type=mediafile[1], media=mediafile[0])
            await bot.send_media_group(chat_id=-channel_id, media=media_group.build())

        else:
            await bot.send_message(chat_id=-channel_id, text=html.quote(publication.get_text()))
        await queue.remove_publication(removing_index=0)

    except IndexError:  # Выскочит если список публикаций пуст
        # Если очередь пуста, просто отключаем ее
        await dict_queue[-channel_id].switch_for_queue()
        # И уведомляем всех администраторов
        channel_name = (await bot.get_chat(chat_id=-channel_id)).title
        msg_text = (f'Очередь публикаций канала <b>{html.quote(channel_name)}</b> '
                    f'остановлена из-за отсутствия в ней публикаций')
        for admin in admins_id:
            try:
                await bot.send_message(chat_id=admin, text=msg_text)
            except TelegramForbiddenError:
                # В списке ID администраторов будет и ID самого бота.
                # И при попытке отправить сообщение самому себе выскочит это исключение
                pass


async def create_publish_queue():
    """Функция запускает очереди публикаций для уже имеющихся каналов при запуске бота"""
    channels = await db.get_channel_list()
    for channel in channels:
        dict_queue[channel['channel_id']] = AutoPosting(str(abs(channel['channel_id'])))
        await dict_queue[channel['channel_id']].upload_queue_info()
        await db.create_publication_table(channel['channel_id'])
        await dict_queue[channel['channel_id']].upload_list_of_publication()


async def add_queue(chnl_id: int):
    """Функция добавляет очередь публикаций для новых каналов"""
    dict_queue[chnl_id] = AutoPosting(str(abs(chnl_id)))
    await db.create_publication_table(chnl_id)


async def delete_queue(chnl_id: int):
    """Функция удаляет очередь публикаций и все что с ней связано при удалении канала"""
    dict_queue.pop(chnl_id)
    await db.delete_jobstore_table(channel_id=chnl_id)
    await db.delete_publication_table(channel_id=chnl_id)


class AutoPosting:
    """Класс позволяет реализовать отдельную очередь публикаций для каждой группы"""

    def __init__(self, chn_id: str) -> None:
        self._scheduler = AsyncIOScheduler(gconfig={'apscheduler.timezone': 'Europe/Moscow'})
        self._scheduler.add_jobstore(jobstore='sqlalchemy', alias=f'{chn_id}', url=PG_URI, tablename=f'aps{chn_id}')
        self._alias = f'{chn_id}'  # Свой псевдоним, что бы использовать его и не передавать каждый раз заново
        self._trigger_settings = None
        self._running = True
        self.queue_info = None

        self. _publication_list = list()
        self._scheduler.start()

    async def adding_publication_in_queue(self, file_id=None, text=None):
        """Метод сохраняет публикацию в список публикаций через специальный контейнер"""
        container_id = str(int(time.time()))  # В качестве ID будут секунды в виде строки
        content_container = ContentContainer(container_id=container_id, file_id=file_id, text=text)
        self._publication_list.append(content_container)

        if file_id:
            file_id_for_db = ''
            for file in file_id:
                file_id_for_db += '!$!$'.join(file)
                file_id_for_db += '$!$!'  # разделитель между записями
            file_id = file_id_for_db

        await db.save_publication(channel_id=int(self._alias), container_id=container_id,
                                  file_id=file_id, publication_text=text)

    async def get_list_publication(self):
        """Возвращает список публикаций"""
        return self._publication_list

    async def get_queue_status(self):
        """Возвращает состояние активности очереди публикаций"""
        return 'Активна' if self._running else 'Отключена'

    async def switch_for_queue(self):
        """Делает ВКЛ/ВЫКЛ для очередей публикаций"""
        if self._running:
            self._scheduler.pause()
            self._running = False
        else:
            self._scheduler.resume()
            self._running = True

    async def save_trigger_setting(self, trigger_data):
        """Здесь настройки для триггера сохраняются в самом инстансе.
        Так же сохраняет строку с информацией, что бы после перезапуска бота можно было
        вывести актуальную информацию без перенастройки"""
        self._trigger_settings = trigger_data
        await db.save_queue_info(int(self._alias), self.queue_info)

    async def get_queue_info(self, chnl_name):
        """Здесь формируется строка необходимая для отображения установленных настроек очереди публикаций"""

        # Если self.queue_info == None значит настройки еще не производились или
        # их нужно загрузить из БД после перезапуска бота

        if self.queue_info:
            queue_info_str = self.queue_info.split('_')

            # Если в списке queue_info_str два элемента (дни и время) значит это настройки для триггера класса cron

            if len(queue_info_str) > 1:
                queue_info_str = [queue_info_str[0].split(), queue_info_str[1].split()]
                day_str = ''
                time_str = ''
                for day in queue_info_str[0]:
                    day_str += day + ' '
                for tm in queue_info_str[1]:
                    time_str += tm + ' '

                ready_string = (f'Очередь публикаций канала <i><b>{html.quote(chnl_name)}</b></i>\n\n'
                                f'Основной принцип работы: <b>По дням недели</b>\n'
                                f'Выбранные дни: <b>{day_str}</b>\n'
                                f'Выбранное время: <b>{time_str}</b>')

                return ready_string

            # В ином случае это триггер interval (только время)
            else:
                ready_string = (f'Очередь публикаций канала <i><b>{html.quote(chnl_name)}</b></i>\n\n'
                                f'Основной принцип работы: <b>Определенным интервалом</b>\n'
                                f'Установленный интервал: <b>{queue_info_str[0]}</b>')

                return ready_string

        else:
            return 'Очередь еще не настроена!'

    async def set_trigger(self):
        """Здесь формируется настройки для очереди публикаций"""
        # Сначала чистим исполнитель от уже установленных задач
        task_to_be_deleted = self._scheduler.get_jobs(jobstore=self._alias)
        for task in task_to_be_deleted:
            self._scheduler.remove_job(job_id=task.id, jobstore=self._alias)

        #  Если self.trigger_settings является списком, значит триггер будет cron
        if isinstance(self._trigger_settings, list):
            days = ','.join(self._trigger_settings[0])
            selected_time = self._trigger_settings[1]

            for time_ex in selected_time:
                time_execute = time_ex.split(':')
                job_id = '_'.join([self._alias, time_ex])
                self._scheduler.add_job(func=publish_post, kwargs={'channel_id': int(self._alias)}, trigger='cron',
                                        day_of_week=days, hour=time_execute[0], minute=time_execute[1],
                                        jobstore=self._alias, id=job_id, max_instances=1,
                                        replace_existing=True)

        # Если self.trigger_settings является строкой, значит триггер будет interval
        elif isinstance(self._trigger_settings, str):
            time_execute = self._trigger_settings.split(':')
            job_id = '_'.join([self._alias, 'interval'])
            self._scheduler.add_job(func=publish_post, kwargs={'channel_id': int(self._alias)}, trigger='interval',
                                    hours=int(time_execute[0]), minutes=int(time_execute[1]),
                                    jobstore=self._alias, id=job_id, max_instances=1,
                                    replace_existing=True)

        else:
            print('TriggerError')

    async def upload_queue_info(self):
        """Здесь происходит выгрузка информации об очереди публикации если таковая имеется"""
        try:
            self.queue_info = (await db.get_queue_info(int(self._alias)))[0]['settings_info']
        # Если и в БД пусто, то вылезет ошибка. Проигнорируем её
        except IndexError:
            pass

    async def upload_list_of_publication(self):
        """Здесь выгружаются публикации из БД в список публикаций"""
        list_from_db = await db.get_list_of_publication(channel_id=int(self._alias))
        for publication in list_from_db:
            if publication['file_id'] != 'None':

                file_id = publication['file_id'].split('$!$!')
                file_id = [elem.split('!$!$') for elem in file_id]
                file_id.pop()  # В конце образуется пустой элемент
            else:
                file_id = None
            content_container = ContentContainer(container_id=publication['container_id'],
                                                 file_id=file_id,
                                                 text=(publication['publication_text']
                                                       if publication['publication_text'] != 'None' else None))

            self._publication_list.append(content_container)

    async def remove_publication(self, removing_index):
        """Метод удаляет запись из списка публикаций по индексу"""
        try:
            # Удаляем из самого списка
            removing_container = self._publication_list.pop(removing_index)
            # И удаляем из БД
            await db.remove_publication_from_db(channel_id=int(self._alias), container_id=removing_container.get_id())
        except IndexError:  # На случай исключительного "маразма"
            pass
