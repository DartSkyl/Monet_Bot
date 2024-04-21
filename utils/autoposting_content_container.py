class ContentContainer:
    """Через данный класс реализуется контейнер для контента будущей публикации"""
    def __init__(self, container_id, file_id, text):
        self._id = container_id
        self._file_id = file_id
        self._text = text

    def __str__(self):
        itself_str = f'\nID: {self._id}\nFile ID: {self._file_id}\nText: {self._text}\n'
        return itself_str

    def get_id(self):
        return self._id

    def get_file_id(self):
        return self._file_id

    def get_text(self):
        return self._text

    def get_info(self):
        info_string = '<i>Текст публикации:</i>\n{text}'.format(
            text=self._text if self._text else '<i><b>Отсутствует</b></i>'
        )
        return info_string
