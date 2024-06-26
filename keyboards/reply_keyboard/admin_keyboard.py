from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, ReplyKeyboardMarkup

# ========== Главная клавиатура администратора ==========

# main_admin_keyboard = ReplyKeyboardBuilder()

main_buttons = [
        [KeyboardButton(text='📝 Управление каналами'),
         KeyboardButton(text='⌛ Управление подписками')],
        [KeyboardButton(text='📜 Автопостинг '),
         KeyboardButton(text='📈 Статистика')],
        [KeyboardButton(text='⚙️ Настройка пользовательских сообщений')]
]
main_admin_keyboard = ReplyKeyboardMarkup(keyboard=main_buttons, resize_keyboard=True)
# main_admin_keyboard.add(*main_buttons)
# main_admin_keyboard.adjust(1)
# main_admin_keyboard = main_admin_keyboard.as_markup(resize_keyboard=True)


users_msg_buttons = [
    [KeyboardButton(text='📄 Системные сообщения'),
     KeyboardButton(text='📝 Описание каналов')],
    [KeyboardButton(text='📩 Установить контакт для подписчиков')],
    [KeyboardButton(text='Назад')]
]

users_msg_markup = ReplyKeyboardMarkup(keyboard=users_msg_buttons, resize_keyboard=True)

# ========== Клавиатура управления группами ==========

group_management = ReplyKeyboardBuilder()

gm_buttons = [
    KeyboardButton(text='📃 Список каналов'),
    KeyboardButton(text='➕ Добавить открытый канал'),
    KeyboardButton(text='➕➕ Добавить платный канал'),
    KeyboardButton(text='➖ Удалить канал'),
    KeyboardButton(text='Назад')
]

group_management.add(*gm_buttons)
group_management.adjust(2)
group_management = group_management.as_markup(resize_keyboard=True)

# ========== Клавиатура управления подписками ==========

sub_manag = ReplyKeyboardBuilder()

sm_buttons = [
    KeyboardButton(text='⏲️ Изменить период пробной подписки'),
    KeyboardButton(text='💵 Добавить платную подписку'),
    KeyboardButton(text='⚙️ Посмотреть/удалить установленные подписки'),
    KeyboardButton(text='➕ Добавить подписку пользователю'),
    KeyboardButton(text='Назад'),
]

sub_manag.add(*sm_buttons)
sub_manag.adjust(1)
sub_manag = sub_manag.as_markup(resize_keyboard=True)

# ========== Клавиатура меню авто постинга ==========

auto_posting = ReplyKeyboardBuilder()

ap_buttons = [
    KeyboardButton(text='📅 Посмотреть очередь публикаций'),
    KeyboardButton(text='⚙️ Настройка очереди публикаций'),
    KeyboardButton(text='➕ Добавить публикацию в очередь'),
    KeyboardButton(text='⏯️ Включить / Выключить очередь публикаций'),
    KeyboardButton(text='Назад'),
]

auto_posting.add(*ap_buttons)
auto_posting.adjust(1)
auto_posting = auto_posting.as_markup(resize_keyboard=True)

only_text = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Дальше')]],
    resize_keyboard=True
)

only_file = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Готово'), KeyboardButton(text='🚫 Отмена')]],
    resize_keyboard=True
)

# ========== Кнопки отмены ==========

cancel_button = ReplyKeyboardBuilder()
c_button = [KeyboardButton(text='🚫 Отмена')]
cancel_button.add(*c_button)
cancel_button = cancel_button.as_markup(resize_keyboard=True)

cancel_button_2 = ReplyKeyboardBuilder()
c_button = [
            KeyboardButton(text='✔️ Готово'),
            KeyboardButton(text='🚫 Отмена')
            ]
cancel_button_2.add(*c_button)
cancel_button_2 = cancel_button_2.as_markup(resize_keyboard=True)

returning_button = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='⏪ Вернуться')]], resize_keyboard=True
)
