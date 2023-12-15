from loader import bot


async def publish_post(channel_id: int):
    """Данная функция отвечает за публикацию постов в каналах, привязанных к боту.
    На входе получает только ID канала"""
    await bot.send_message(chat_id=-channel_id)  # Так как ID каналов это отрицательное число


class PublishController:
    def __init__(self):
        pass
