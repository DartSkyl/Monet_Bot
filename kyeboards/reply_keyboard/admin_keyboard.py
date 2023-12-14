from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# ========== Главная клавиатура администратора ==========

main_admin_keyboard = ReplyKeyboardBuilder()

main_buttons = [
        KeyboardButton(text='📝 Управление каналами'),
        KeyboardButton(text='⌛ Управление подписками'),
        KeyboardButton(text='📜 Авто постинг '),
        KeyboardButton(text='📈 Статистика')
]

main_admin_keyboard.add(*main_buttons)
main_admin_keyboard.adjust(1)
main_admin_keyboard = main_admin_keyboard.as_markup(resize_keyboard=True)

# ========== Клавиатура управления группами ==========

group_management = ReplyKeyboardBuilder()

gm_buttons = [
    KeyboardButton(text='📃 Список каналов'),
    KeyboardButton(text='➕ Добавить открытый канал'),
    KeyboardButton(text='➕➕ Добавить закрытый канал'),
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
    KeyboardButton(text='➖ Удалить публикацию из очереди'),
    KeyboardButton(text='Назад'),
]

auto_posting.add(*ap_buttons)
auto_posting.adjust(1)
auto_posting = auto_posting.as_markup(resize_keyboard=True)

# ========== Кнопка отмены ==========

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
