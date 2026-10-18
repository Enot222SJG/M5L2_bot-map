import telebot
import os
from config import *
from logic import *

bot = telebot.TeleBot(TOKEN)
manager = DB_Map(DATABASE)
manager.create_user_table()

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id,
                     "Привет! Я бот, который может показывать города на карте.\n"
                     "Напиши /help для списка команд.")

@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.send_message(message.chat.id,
                     "Доступные команды:\n"
                     "/start — начать работу с ботом\n"
                     "/help — список команд\n"
                     "/show_city <город> — показать город на карте\n"
                     "/remember_city <город> — сохранить город\n"
                     "/show_my_cities — показать все сохранённые города на карте")


@bot.message_handler(commands=['show_city'])
def handle_show_city(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id,
                         "Укажи название города после команды.\n"
                         "Пример: /show_city London")
        return

    city_name = parts[1].strip()
    coords = manager.get_coordinates(city_name)

    if not coords:
        bot.send_message(message.chat.id,
                         "Такого города я не знаю. Убедись, что он написан на английском!")
        return

    # Генерируем карту с одним городом
    path = f"map_{message.chat.id}.png"
    result = manager.create_grapf(path, [city_name])

    if result:
        with open(path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=f"Город {city_name} на карте")
        os.remove(path)
    else:
        bot.send_message(message.chat.id, "Не удалось создать карту.")


@bot.message_handler(commands=['remember_city'])
def handle_remember_city(message):
    user_id = message.chat.id
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id,
                         "Укажи название города после команды.\n"
                         "Пример: /remember_city London")
        return

    city_name = parts[1].strip()
    if manager.add_city(user_id, city_name):
        bot.send_message(message.chat.id, f'Город {city_name} успешно сохранен!')
    else:
        bot.send_message(message.chat.id,
                         'Такого города я не знаю. Убедись, что он написан на английском!')

@bot.message_handler(commands=['show_my_cities'])
def handle_show_visited_cities(message):
    cities = manager.select_cities(message.chat.id)

    if not cities:
        bot.send_message(message.chat.id,
                         "У тебя пока нет сохранённых городов.\n"
                         "Используй /remember_city <город>, чтобы добавить.")
        return

    # Генерируем карту со всеми городами пользователя
    path = f"map_{message.chat.id}.png"
    result = manager.create_grapf(path, cities)

    if result:
        city_list = ", ".join(cities)
        with open(path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo,
                           caption=f"Твои города: {city_list}")
        os.remove(path)
    else:
        bot.send_message(message.chat.id, "Не удалось создать карту.")


if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling()
