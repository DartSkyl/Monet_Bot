from aiogram import html


types_dict = {
        'text': 'Текст',
        'pic': 'Картинка',
        'pic_text': 'Картинка + Текст',
        'video': 'Видео',
        'video_text': 'Видео + Текст',
        'file': 'Файл',
        'file_text': 'Файл + Текст',
        'video_note': 'Видеосообщение',
    }


class ContentContainer:
    """Через данный класс реализуется контейнер для контента будущей публикации"""
    def __init__(self, container_id, post_type, file_id=None, text=None):
        self._id = container_id
        self._type = post_type
        self._file_id = file_id
        self._text = text

    def __str__(self):
        itself_str = f'\nID: {self._id}\nType: {self._type}\nFile ID: {self._file_id}\nText: {self._text}\n'
        return itself_str

    def get_id(self):
        return self._id

    def get_type(self):
        return self._type

    def get_file_id(self):
        return self._file_id

    def get_text(self):
        return self._text

    def get_info(self):
        info_string = '<i>Тип публикации:</i> <b>{post_type}</b>\n\n<i>Текст публикации:</i>\n{text}'.format(
            post_type=types_dict[self._type],
            text=(html.quote(self._text) if self._text else '<i><b>Отсутствует</b></i>')
        )
        return info_string
