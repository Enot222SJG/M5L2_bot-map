import telebot
import os
from config import *
from logic import *

bot = telebot.TeleBot(TOKEN)
manager = DB_Map(DATABASE)
manager.create_user_table()

AVAILABLE_COLORS = {
    'красный': 'red',
    'синий': 'blue',
    'зелёный': 'green',
    'зеленый': 'green',
    'жёлтый': 'yellow',
    'желтый': 'yellow',
    'оранжевый': 'orange',
    'фиолетовый': 'purple',
    'чёрный': 'black',
    'черный': 'black',
    'белый': 'white',
    'розовый': 'pink',
    'red': 'red',
    'blue': 'blue',
    'green': 'green',
    'yellow': 'yellow',
    'orange': 'orange',
    'purple': 'purple',
    'black': 'black',
    'white': 'white',
    'pink': 'pink',
}


@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id,
                     "Привет! Я бот, который показывает города на карте.\n"
                     "Можно писать названия городов на русском или английском.\n"
                     "Напиши /help для списка команд.")


@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.send_message(message.chat.id,
                     "Доступные команды:\n\n"
                     "/start — запуск бота\n"
                     "/help — список команд\n"
                     "/show_city <город> — показать город на карте\n"
                     "/remember_city <город> — сохранить город\n"
                     "/show_my_cities — все сохранённые города на карте\n"
                     "/set_color <цвет> — выбрать цвет маркеров\n\n"
                     "Города можно писать на русском: /show_city Москва")


@bot.message_handler(commands=['set_color'])
def handle_set_color(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        colors_list = ', '.join(sorted(set(AVAILABLE_COLORS.values())))
        bot.send_message(message.chat.id,
                         f"Укажи цвет после команды.\n"
                         f"Доступные цвета: {colors_list}\n"
                         f"Можно на русском: /set_color красный")
        return

    color_input = parts[1].strip().lower()
    color = AVAILABLE_COLORS.get(color_input)

    if not color:
        bot.send_message(message.chat.id, "Такого цвета нет. Напиши /set_color чтобы увидеть список.")
        return

    manager.set_color(message.chat.id, color)
    bot.send_message(message.chat.id, f"Цвет маркеров изменён на {color}!")


@bot.message_handler(commands=['show_city'])
def handle_show_city(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id,
                         "Укажи город после команды.\n"
                         "Пример: /show_city Лондон")
        return

    city_name = parts[1].strip()
    coords = manager.get_coordinates(city_name)

    if not coords:
        bot.send_message(message.chat.id,
                         "Такого города я не знаю. Попробуй другое написание.")
        return

    color = manager.get_color(message.chat.id)
    path = f"map_{message.chat.id}.png"
    result = manager.create_grapf(path, [city_name], marker_color=color)

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
                         "Укажи город после команды.\n"
                         "Пример: /remember_city Париж")
        return

    city_name = parts[1].strip()
    result = manager.add_city(user_id, city_name)
    if result:
        bot.send_message(message.chat.id, f'Город {city_name} ({result}) сохранён!')
    else:
        bot.send_message(message.chat.id,
                         'Такого города я не знаю. Попробуй другое написание.')


@bot.message_handler(commands=['show_my_cities'])
def handle_show_visited_cities(message):
    cities = manager.select_cities(message.chat.id)

    if not cities:
        bot.send_message(message.chat.id,
                         "У тебя пока нет сохранённых городов.\n"
                         "Используй /remember_city <город>, чтобы добавить.")
        return

    color = manager.get_color(message.chat.id)
    path = f"map_{message.chat.id}.png"
    result = manager.create_grapf(path, cities, marker_color=color)

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
