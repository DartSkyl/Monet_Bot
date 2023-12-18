import logging
from config_data.config import PG_URI
from loader import db

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
    print(f'Works! Channel ID: {-channel_id}')


async def create_publish_queue():
    channels = await db.get_channel_list()
    for channel in channels:
        dict_queue[channel['channel_id']] = AutoPosting(abs(channel['channel_id']))
        await dict_queue[channel['channel_id']].upload_queue_info()
    _general_scheduler.start()


async def add_queue(chnl_id: int):
    dict_queue[chnl_id] = AutoPosting(str(abs(chnl_id)))


async def delete_queue(chnl_id: int):
    dict_queue.pop(chnl_id)
    _general_scheduler.remove_jobstore(alias=f'{abs(chnl_id)}')
    _general_scheduler.remove_executor(alias=f'{abs(chnl_id)}')
    await db.delete_jobstore_table(channel_id=chnl_id)


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
                                f'Основной принцип работы: <b>Определенным интервалом</b>'
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

            self._scheduler.print_jobs(jobstore=self._alias)

        # Если self.trigger_settings является строкой, значит триггер будет interval
        elif isinstance(self._trigger_settings, str):
            time_execute = self._trigger_settings.split(':')
            job_id = '_'.join([self._alias, 'interval'])
            self._scheduler.add_job(func=publish_post, kwargs={'channel_id': int(self._alias)}, trigger='interval',
                                    hours=int(time_execute[0]), minutes=int(time_execute[1]),
                                    jobstore=self._alias, executor=self._alias, id=job_id, max_instances=1,
                                    replace_existing=True)

            self._scheduler.print_jobs(jobstore=self._alias)

        else:
            print('TriggerError')

    async def upload_queue_info(self):
        """Здесь происходит выгрузка информации об очереди публикации если таковая имеется"""
        try:
            self.queue_info = (await db.get_queue_info(int(self._alias)))[0]['settings_info']
        # Если и в БД пусто, то вылезет ошибка. Проигнорируем её
        except IndexError:
            pass
