import time


class ContentContainer:
    """Через данный класс реализуется контейнер для контента будущей публикации"""
    def __init__(self, post_type, file_id=None, text=None):
        self._id = str(int(time.time()))
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
