import logging
import time
from config_data.config import PG_URI
from loader import db, bot
from .autoposting_content_container import ContentContainer

from apscheduler.events import EVENT_JOB_MISSED, EVENT_JOB_ERROR
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.asyncio import AsyncIOExecutor

from aiogram import html


def my_listener(event):
    if event.code == EVENT_JOB_MISSED:
        print('Missed')
    else:
        print('Error')


logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

dict_queue = dict()

_general_scheduler = AsyncIOScheduler()
_general_scheduler.add_listener(my_listener, EVENT_JOB_MISSED | EVENT_JOB_ERROR)


async def publish_post(channel_id: int):
    """Данная функция отвечает за публикацию постов в каналах, привязанных к боту.
    На входе получает только ID канала"""
    try:
        queue = dict_queue[-channel_id]
        publication = (await queue.get_list_publication())[0]
        publication_type = publication.get_type()
        # Иначе могут быть проблемы с парсингом сообщений:
        publication_text = (html.quote(publication.get_text()) if publication.get_text() else None)
        publication_file_id = publication.get_file_id()

        if publication_type == 'text':
            await bot.send_message(chat_id=-channel_id, text=publication_text)
        elif publication_type in ['pic', 'pic_text']:
            await bot.send_photo(chat_id=-channel_id, photo=publication_file_id, caption=publication_text)
        elif publication_type in ['video', 'video_text']:
            await bot.send_video(chat_id=-channel_id, video=publication_file_id, caption=publication_text)
        elif publication_type in ['file', 'file_text']:
            await bot.send_document(chat_id=-channel_id, document=publication_file_id, caption=publication_text)
        elif publication_type == 'video_note':
            await bot.send_video_note(chat_id=-channel_id, video_note=publication_file_id)
        await queue.remove_publication(removing_index=0)

    except IndexError:  # Выскочит если список публикаций пуст
        print(f'List of publication is empty! Channel ID: {-channel_id}')



async def create_publish_queue():
    """Функция запускает очереди публикаций для уже имеющихся каналов при запуске бота"""
    channels = await db.get_channel_list()
    for channel in channels:
        dict_queue[channel['channel_id']] = AutoPosting(str(abs(channel['channel_id'])))
        await dict_queue[channel['channel_id']].upload_queue_info()
        await db.create_publication_table(channel['channel_id'])
        await dict_queue[channel['channel_id']].upload_list_of_publication()
    _general_scheduler.start()


async def add_queue(chnl_id: int):
    """Функция добавляет очередь публикаций для новых каналов"""
    dict_queue[chnl_id] = AutoPosting(str(abs(chnl_id)))
    await db.create_publication_table(chnl_id)


async def delete_queue(chnl_id: int):
    """Функция удаляет очередь публикаций и все что с ней связано при удалении канала"""
    dict_queue.pop(chnl_id)
    _general_scheduler.remove_jobstore(alias=f'{abs(chnl_id)}')
    _general_scheduler.remove_executor(alias=f'{abs(chnl_id)}')
    await db.delete_jobstore_table(channel_id=chnl_id)
    await db.delete_publication_table(channel_id=chnl_id)


class AutoPosting:
    """Класс позволяет реализовать отдельную очередь публикаций для каждой группы"""

    def __init__(self, chn_id: str) -> None:
        """Планировщик общий для всех. Отельными будут хранилища заданий и экзекуторы"""

        # Часовой пояс!!!!!!

        self._scheduler = _general_scheduler
        self._scheduler.add_jobstore(jobstore='sqlalchemy', alias=f'{chn_id}', url=PG_URI, tablename=f'aps{chn_id}')
        self._executor = AsyncIOExecutor()
        self._scheduler.add_executor(executor=self._executor, alias=f'{chn_id}')
        self._executor.start(scheduler=self._scheduler, alias=f'{chn_id}')
        self._alias = f'{chn_id}'  # Свой псевдоним, что бы использовать его и не передавать каждый раз заново
        self._trigger_settings = None
        self.queue_info = None

        self. _publication_list = list()

    async def adding_publication_in_queue(self, content_type, file_id=None, text=None):
        """Метод сохраняет публикацию в список публикаций через специальный контейнер"""
        content_container = None  # Изменим это чуть ниже, в зависимости от условий
        container_id = str(int(time.time()))  # В качестве ID будут секунды в виде строки
        if file_id and text:
            content_container = ContentContainer(container_id=container_id, post_type=content_type, file_id=file_id, text=text)
        elif file_id:
            content_container = ContentContainer(container_id=container_id, post_type=content_type, file_id=file_id)
        elif text:
            content_container = ContentContainer(container_id=container_id, post_type=content_type, text=text)

        self._publication_list.append(content_container)
        await db.save_publication(channel_id=int(self._alias), container_id=container_id,
                                  content_type=content_type, file_id=file_id, publication_text=text)


    async def get_list_publication(self):
        """Возвращает список публикаций"""
        return self._publication_list

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
                                        jobstore=self._alias, executor=self._alias, id=job_id, max_instances=1,
                                        replace_existing=True)

        # Если self.trigger_settings является строкой, значит триггер будет interval
        elif isinstance(self._trigger_settings, str):
            time_execute = self._trigger_settings.split(':')
            job_id = '_'.join([self._alias, 'interval'])
            self._scheduler.add_job(func=publish_post, kwargs={'channel_id': int(self._alias)}, trigger='interval',
                                    hours=int(time_execute[0]), minutes=int(time_execute[1]),
                                    jobstore=self._alias, executor=self._alias, id=job_id, max_instances=1,
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
            content_container = ContentContainer(container_id=publication['container_id'],
                                                 post_type=publication['content_type'],
                                                 file_id=(publication['file_id']
                                                          if publication['file_id'] != 'None' else None),
                                                 # Что бы не передавать 'None' в качестве строки, так как
                                                 # из БД будет загружаться именно такая строка,
                                                 # если текст или ID файла не передавались
                                                 text=(publication['publication_text']
                                                       if publication['publication_text'] != 'None' else None))

            self._publication_list.append(content_container)

    async def remove_publication(self, removing_index):
        """Метод удаляет из списка публикаций опубликованную запись.
        Так как публикуемая запись всегда имеет индекс 0 то ее и будем удалять"""
        try:
            # Удаляем из самого списка
            removing_container = self._publication_list.pop(removing_index)
            # И удаляем из БД
            await db.remove_publication_from_db(channel_id=int(self._alias), container_id=removing_container.get_id())
        except IndexError:  # На случай исключительного "маразма"
            pass
