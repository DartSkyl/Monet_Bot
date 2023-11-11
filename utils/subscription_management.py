import time
from asyncio import sleep
from loader import bot, db, channels_dict, subscription_dict


async def cycle_controlling_subscriptions_start() -> None:
    await cycle_controlling_subscriptions()


async def cycle_controlling_subscriptions() -> None:
    """Данная функция с определенной периодичностью проверяет состояние подписки пользователей"""
    while True:
        print('\nNew cycle\n')
        # Проходимся по всем закрытым каналам
        for ch_id in channels_dict['is_paid']:
            # Формируем список из пользователей и окончаний их подписки
            s_lst = await SubManag.check_subscription(channel_id=ch_id)
            if len(s_lst) > 0:  # Данная проверка нужна, на случай если в группе еще никого нет и список по ней пуст
                # Смотрим, через сколько заканчивается подписка
                test_sub = int(s_lst[0]['end_of_subscription']) - int(time.time())
                if test_sub > 0:
                    print(test_sub)
                else:
                    await bot.ban_chat_member(chat_id=ch_id, user_id=s_lst[0]['user_id'])
                    print('Kicked!')
        # В скобочках асинхронной функции sleep(), в секундах, указана периодичность,
        # с которой цикл проверяет подписки по всем группам и пользователям
        await sleep(60)


class SubManag:
    """Через данный класс буду реализованы методы для управления подписками"""

    @staticmethod
    async def trail_sub_period_TEST():
        subscription_dict['0'] = 600

    @staticmethod
    async def trail_sub_period(period: int):
        """В этом методе устанавливается пробный период подписки"""
        # Администратор указывает количество дней в пробном периоде
        # далее умножаем это число на количество секунд в сутках
        subscription_dict['0'] = 60*60*24*period
        # Не забываем, что в БД и в оперативной памяти под ключом 0 хранится пробный период в секундах
        await db.set_sub_setting(period='0', cost=subscription_dict['0'])

    @staticmethod
    async def add_user_trail_sub(user_id: int, channel_id: int) -> None:
        """Метод включает новому пользователю пробную подписку """
        # Сначала добавляем пользователя в базу с пробниками
        await db.add_user_trail_subscription(user_id=user_id, channel_id=channel_id)
        # Затем добавляем в основную таблицу канала
        await db.add_user_in_paid_channel(
            user_id=user_id,
            channel_id=channel_id,
            subscription=subscription_dict['0']
        )
        print(subscription_dict['0'])

    @staticmethod
    async def check_subscription(channel_id) -> list:
        sub_list = await db.list_of_user_subscriptions(channel_id=channel_id)
        return sub_list

    @staticmethod
    async def get_trail_period() -> int:
        return int(subscription_dict['0'] / (60*60*24))

    @staticmethod
    async def set_paid_subscription(period, cost) -> None:
        subscription_dict[period] = cost
        await db.set_sub_setting(period=period, cost=cost)

    @staticmethod
    async def delete_subscription(period) -> None:
        subscription_dict.pop(period)
        await db.delete_subscription(period=period)

    @staticmethod
    async def add_user_paid_sub(user_id: int, channel_id: int, period: int) -> None:
        user_info = await db.get_user_from_channel(user_id=user_id, channel_id=channel_id)
        if len(user_info) > 0:  # Проверяем, есть ли такой пользователь в базе
            # На всякий случай убедимся, что подписка у него еще действует
            if user_info[0]['end_of_subscription'] > int(time.time()):
                new_sub = user_info[0]['end_of_subscription'] + ((60*60*24) * period)
                await db.subscription_update(user_id=user_id, channel_id=channel_id, new_sub=new_sub)
            else:  # Если вдруг его подписка уже не активна, хотя таких записей в БД быть не должно
                new_sub = int(time.time()) + ((60*60*24) * period)
                await db.subscription_update(user_id=user_id, channel_id=channel_id, new_sub=new_sub)
        else:  # Если пользователя нет в БД
            new_sub = (60*60*24) * period
            await db.add_user_in_paid_channel(user_id=user_id, channel_id=channel_id, subscription=new_sub)


