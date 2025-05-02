
import telebot
from telebot import types
from db_manager import DBManager  # Убедитесь, что файл называется db_manager.py

# Замените на свой токен
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Создаем бота
bot = telebot.TeleBot(BOT_TOKEN)

# Создаем экземпляр DBManager
db = DBManager()

# --- Хендлеры для обычных пользователей ---

@bot.message_handler(commands=['start'])
def start(message):
    db.add_user(message.from_user.id, message.from_user.username)  # Добавляем пользователя в БД
    bot.reply_to(message, f"Привет, {message.from_user.username}! Твой баланс: {db.get_user_balance(message.from_user.id)} монет.")

@bot.message_handler(commands=['balance'])
def get_balance(message):
    balance = db.get_user_balance(message.from_user.id)
    bot.reply_to(message, f"Твой баланс: {balance} монет.")

@bot.message_handler(commands=['bonus'])
def show_bonus_options(message):
    # TODO: Реализуйте логику предоставления бонусов за монеты.
    bot.reply_to(message, "В разработке...")

# --- Хендлеры для администраторов ---
# Проверка на админа
def is_admin(message):
    return db.is_admin(message.from_user.id)

# Декоратор для проверки на админа
def admin_required(func):
    def wrapper(message):
        if is_admin(message):
            func(message)
        else:
            bot.reply_to(message, "У вас нет прав администратора.")
    return wrapper

@bot.message_handler(commands=['admin'])
@admin_required
def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    item1 = types.KeyboardButton("Настройки бота")
    item2 = types.KeyboardButton("Добавить картинку")
    item3 = types.KeyboardButton("Список картинок")
    markup.add(item1, item2, item3)

    bot.send_message(message.chat.id, "Добро пожаловать в админ-панель!", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Настройки бота")
@admin_required
def bot_settings(message):
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
  item1 = types.KeyboardButton("Изменить период отправки")
  item2 = types.KeyboardButton("Изменить размер бонусов")
  back = types.KeyboardButton("Назад")
  markup.add(item1, item2, back)
  bot.send_message(message.chat.id, "Выберите настройку:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Изменить период отправки")
@admin_required
def change_period(message):
  # TODO: Реализовать логику изменения периода отправки сообщений.
  bot.send_message(message.chat.id, "В разработке...")

@bot.message_handler(func=lambda message: message.text == "Изменить размер бонусов")
@admin_required
def change_bonus_size(message):
    # TODO: Реализовать логику изменения размера бонусов.
    bot.send_message(message.chat.id, "В разработке...")


@bot.message_handler(func=lambda message: message.text == "Добавить картинку", content_types=['text'])
@admin_required
def ask_for_image(message):
    bot.send_message(message.chat.id, "Отправьте изображение, которое хотите добавить.")
    bot.register_next_step_handler(message, add_image_step)

@admin_required
def add_image_step(message):
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id  # Берем самое большое разрешение
        db.add_image(file_id)
        bot.reply_to(message, "Изображение добавлено! Вы можете добавить описание, отправив его следующим сообщением (или пропустить).")
        bot.register_next_step_handler(message, save_image_description, file_id)
    else:
        bot.reply_to(message, "Пожалуйста, отправьте изображение.")


@admin_required
def save_image_description(message, file_id):
    if message.content_type == 'text':
        db.cursor.execute("UPDATE admin_images SET description = ? WHERE file_id = ?", (message.text, file_id))
        db.conn.commit()
        bot.reply_to(message, "Описание добавлено!")
    else:
        bot.reply_to(message, "Описание не добавлено.")

    # Вернуться в админ-панель
    admin_panel(message)


@bot.message_handler(func=lambda message: message.text == "Список картинок")
@admin_required
def list_images(message):
    images = db.get_all_images()
    if images:
        for image_id, file_id, description in images:
            bot.send_photo(message.chat.id, file_id, caption=f"ID: {image_id}, Описание: {description}")
    else:
        bot.reply_to(message, "Нет добавленных изображений.")

    # Вернуться в админ-панель
    admin_panel(message)


@bot.message_handler(commands=['add_admin'])
@admin_required
def add_admin_command(message):
    if len(message.text.split()) > 1:
        try:
            user_id_to_add = int(message.text.split()[1])
            db.add_admin(user_id_to_add)
            bot.reply_to(message, f"Пользователь с ID {user_id_to_add} теперь администратор.")
        except ValueError:
            bot.reply_to(message, "Неверный формат ID пользователя.")
    else:
        bot.reply_to(message, "Укажите ID пользователя, которого нужно добавить в администраторы.")

@bot.message_handler(commands=['remove_admin'])
@admin_required
def remove_admin_command(message):
    if len(message.text.split()) > 1:
        try:
            user_id_to_remove = int(message.text.split()[1])
            db.remove_admin(user_id_to_remove)
            bot.reply_to(message, f"Пользователь с ID {user_id_to_remove} больше не администратор.")
        except ValueError:
            bot.reply_to(message, "Неверный формат ID пользователя.")
    else:
        bot.reply_to(message, "Укажите ID пользователя, которого нужно удалить из администраторов.")

@bot.message_handler(func=lambda message: message.text == "Назад")
@admin_required
def back_to_admin_panel(message):
    admin_panel(message)

# --- Запуск бота ---
if __name__ == '__main__':
    #  Сразу добавляем себя в админы (замените YOUR_TELEGRAM_USER_ID на свой ID)
    db.add_admin(YOUR_TELEGRAM_USER_ID) # Замените на ваш ID
    bot.infinity_polling()

# После того, как программа отработала, закрываем соединение с базой данных
db.close()
