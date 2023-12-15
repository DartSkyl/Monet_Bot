import time
from loader import bot, db, channels_dict, subscription_dict
from aiogram.exceptions import TelegramBadRequest


from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_MISSED
import logging


logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)


async def cycle_controlling_subscriptions() -> None:
    """Данная функция передается планировщику, в качестве задачи которая проверяет подписку пользователей"""
    print('\nNew cycle\n')
    # Проходимся по всем закрытым каналам
    for ch_id in channels_dict['is_paid']:
        # Формируем список из пользователей и окончаний их подписки
        s_lst = await SubManag.check_subscription(channel_id=ch_id)
        if len(s_lst) > 0:  # Данная проверка нужна, на случай если в группе еще никого нет и список по ней пуст
            for user in s_lst:
                # Смотрим, через сколько заканчивается подписка
                subscription = int(user['end_of_subscription']) - int(time.time())
                if subscription > 0:
                    print(subscription)
                else:
                    try:
                        await bot.ban_chat_member(chat_id=ch_id, user_id=user['user_id'],
                                                  # Разбаним через 60 секунд, что бы после оплаты
                                                  # подписки пользователь мог вернуться
                                                  until_date=(int(time.time()) + 60))
                        await SubManag.delete_user(user_id=user['user_id'], channel_id=ch_id)
                        print(f'User with ID {user["user_id"]} kicked!')
                        # На случай, если пользователя с таким ID больше не существует
                    except TelegramBadRequest as exc:
                        print(f'Пользователя с таким ID ({user["user_id"]}) больше не существует!')
                    finally:
                        await SubManag.delete_user(user_id=user['user_id'], channel_id=ch_id)


async def check_subscription():
    """Функция создает экземпляр планировщика с одной единственной задачей: проверять
    подписки пользователей один раз в заданный промежуток времени.
    Данный планировщик не взаимодействует с другими планировщиками и не имеет постоянного хранилища"""
    sub_scheduler = AsyncIOScheduler(timezone='Europe/Moscow')

    sub_scheduler.add_job(
        func=cycle_controlling_subscriptions,
        trigger='interval', hours=2,  # Проверка происходит каждые два часа
        id='sub_control',
        replace_existing=True
    )

    sub_scheduler.add_listener(missed_exec, EVENT_JOB_MISSED)
    sub_scheduler.start()


def missed_exec(event):
    print('Missed!', event.job_id)


class SubManag:
    """Через данный класс буду реализованы методы для управления подписками"""

    @staticmethod
    async def trail_sub_period(period: int, chn_id: int):
        """В этом методе устанавливается пробный период подписки"""
        # Администратор указывает количество дней в пробном периоде
        # далее умножаем это число на количество секунд в сутках
        try:
            subscription_dict[chn_id][0] = 60 * 60 * 24 * period
            await db.set_sub_setting(chl_id_period=(str(chn_id) + '_' + '0'), cost=subscription_dict[chn_id][0])
        except KeyError as exc:
            print(exc)
            subscription_dict[chn_id] = {0: 60 * 60 * 24 * period}
            await db.set_sub_setting(chl_id_period=(str(chn_id) + '_' + '0'), cost=subscription_dict[chn_id][0])
        # Не забываем, что в оперативной памяти, у каждого канала,
        # под ключом 0 хранится пробный период в секундах

    @staticmethod
    async def add_user_trail_sub(user_id: int, channel_id: int) -> None:
        """Метод включает новому пользователю пробную подписку """
        # Сначала добавляем пользователя в базу с пробниками
        await db.add_user_trail_subscription(user_id=user_id, channel_id=channel_id)
        # Затем добавляем в основную таблицу канала
        await db.add_user_in_paid_channel(
            user_id=user_id,
            channel_id=channel_id,
            subscription=subscription_dict[channel_id][0]
        )
        print(subscription_dict[channel_id][0])

    @staticmethod
    async def check_subscription(channel_id) -> list:
        """Метод возвращает список пользователей и дату окончания их подписки"""
        sub_list = await db.list_of_user_subscriptions(channel_id=channel_id)
        return sub_list

    @staticmethod
    async def set_paid_subscription(channel_id: int, period: int, cost: int) -> None:
        """Метод добавляет вариант платной подписки в БД и оперативную память"""
        subscription_dict[channel_id][int(period)] = cost
        chl_id_prd = '_'.join([str(channel_id), str(period)])
        await db.set_sub_setting(chl_id_period=chl_id_prd, cost=cost)

    @staticmethod
    async def delete_subscription(chl_id: int, period: int) -> None:
        """Метод удаляет вариант платной подписки из БД и оперативной памяти"""
        subscription_dict[chl_id].pop(period)
        for_db = '_'.join([str(chl_id), str(period)])
        await db.delete_subscription(chl_id_period=for_db)

    @staticmethod
    async def add_user_paid_sub(user_id: int, channel_id: int, period: int) -> None:
        """Метод добавления подписки пользователю вручную"""
        user_info = await db.get_user_from_channel(user_id=user_id, channel_id=channel_id)
        if len(user_info) > 0:  # Проверяем, есть ли такой пользователь в базе
            # На всякий случай убедимся, что подписка у него еще действует
            if user_info[0]['end_of_subscription'] > int(time.time()):
                new_sub = user_info[0]['end_of_subscription'] + ((60 * 60 * 24) * period)
                await db.subscription_update(user_id=user_id, channel_id=channel_id, new_sub=new_sub)
            else:  # Если вдруг его подписка уже не активна, хотя таких записей в БД быть не должно
                new_sub = int(time.time()) + ((60 * 60 * 24) * period)
                await db.subscription_update(user_id=user_id, channel_id=channel_id, new_sub=new_sub)
        else:  # Если пользователя нет в БД
            new_sub = (60 * 60 * 24) * period
            await db.add_user_in_paid_channel(user_id=user_id, channel_id=channel_id, subscription=new_sub)

    @staticmethod
    async def delete_user(user_id: int, channel_id: int) -> None:
        """Метод удаления записи пользователя из БД"""
        await db.delete_user_from_channel(user_id=user_id, channel_id=channel_id)

    @staticmethod
    async def clear_channel_subscription(channel_id: int) -> None:
        """Метод зачищает всю информацию о подписках канала из оперативной памяти и БД при удалении канала"""
        try:
            for period in subscription_dict[channel_id]:
                for_db = '_'.join([str(channel_id), str(period)])
                await db.delete_subscription(chl_id_period=for_db)
            subscription_dict.pop(channel_id)
        except KeyError:
            pass
