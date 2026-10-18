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


def send_map(bot, manager, chat_id, cities, caption):
    color = manager.get_color(chat_id)
    path = f"map_{chat_id}.png"
    result = manager.create_grapf(path, cities, marker_color=color)
    if result:
        with open(path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=caption)
        os.remove(path)
        return True
    return False


def parse_numbers(parts, start=1):
    """Парсит 1-2 числа из аргументов; возвращает (min, max) или None."""
    try:
        numbers = [int(p.replace(' ', '').replace('\xa0', ''))
                   for p in parts[start:]]
    except ValueError:
        return None
    if not numbers:
        return None
    if len(numbers) == 1:
        return numbers[0], None
    return min(numbers[0], numbers[1]), max(numbers[0], numbers[1])


def format_population(n):
    return f"{n:,}".replace(',', ' ')


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
                     "/set_color <цвет> — выбрать цвет маркеров\n"
                     "/countries — список стран из базы\n"
                     "/country <страна> [сколько] — города страны на карте\n"
                     "/population <от> [до] — города по плотности населения\n"
                     "/filter <страна> <от> [до] — страна + население\n"
                     "/weather <город[,город...]> — погода в городах\n"
                     "/time <город[,город...]> — время в городах\n\n"
                     "Примеры:\n"
                     "/country Россия 20\n"
                     "/population 20000000 50000000\n"
                     "/filter Япония 1000000\n"
                     "/weather Москва, Париж\n"
                     "/time Нью-Йорк")


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

    if not send_map(bot, manager, message.chat.id, [city_name],
                    f"Город {city_name} на карте"):
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

    city_list = ", ".join(cities)
    if not send_map(bot, manager, message.chat.id, cities,
                    f"Твои города: {city_list}"):
        bot.send_message(message.chat.id, "Не удалось создать карту.")


@bot.message_handler(commands=['countries'])
def handle_countries(message):
    countries = manager.get_countries()
    if not countries:
        bot.send_message(message.chat.id, "База стран пуста.")
        return
    lines = [f"{name} — {cnt}" for name, cnt in countries[:100]]
    text = "Страны в базе (страна — городов):\n\n" + "\n".join(lines)
    if len(countries) > 100:
        text += f"\n... и ещё {len(countries) - 100}"
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['country'])
def handle_country(message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        bot.send_message(message.chat.id,
                         "Укажи страну: /country Россия 20\n"
                         "Список стран: /countries")
        return

    country = parts[1]
    limit = 30
    if len(parts) == 3:
        try:
            limit = min(max(int(parts[2]), 1), 100)
        except ValueError:
            pass

    cities = manager.cities_by_country(country, limit)
    if not cities:
        bot.send_message(message.chat.id,
                         "Не нашёл такой страны или в ней нет городов.\n"
                         "Посмотри список: /countries")
        return

    if not send_map(bot, manager, message.chat.id, cities,
                    f"Городы страны {country} ({len(cities)} шт.)"):
        bot.send_message(message.chat.id, "Не удалось создать карту.")


@bot.message_handler(commands=['population'])
def handle_population(message):
    parts = message.text.split(maxsplit=2)
    numbers = parse_numbers(parts)
    if not numbers:
        bot.send_message(message.chat.id,
                         "Укажи диапазон населения (от и до):\n"
                         "/population 10000000 30000000\n"
                         "Или только минимум: /population 20000000")
        return

    min_pop, max_pop = numbers
    cities = manager.cities_by_population(min_pop, max_pop)
    if not cities:
        bot.send_message(message.chat.id, "Не нашёл городов с таким населением.")
        return

    rng = (f"{format_population(min_pop)} — {format_population(max_pop)}"
           if max_pop else f"от {format_population(min_pop)}")
    if not send_map(bot, manager, message.chat.id, cities,
                    f"Города с населением {rng} ({len(cities)} шт.)"):
        bot.send_message(message.chat.id, "Не удалось создать карту.")


@bot.message_handler(commands=['filter'])
def handle_filter(message):
    parts = message.text.split(maxsplit=3)
    if len(parts) < 3:
        bot.send_message(message.chat.id,
                         "Укажи страну и диапазон населения:\n"
                         "/filter Япония 1000000 5000000\n"
                         "Или только минимум: /filter Россия 20000000")
        return

    country = parts[1]
    numbers = parse_numbers(parts, start=2)
    if not numbers:
        bot.send_message(message.chat.id, "После страны укажи числа: /filter Япония 1000000")
        return

    min_pop, max_pop = numbers
    cities = manager.cities_by_country_and_population(country, min_pop, max_pop)
    if not cities:
        bot.send_message(message.chat.id,
                         "Не нашёл городов по этим условиям.\n"
                         "Проверь страну (/countries) и диапазон населения.")
        return

    rng = (f"{format_population(min_pop)} — {format_population(max_pop)}"
           if max_pop else f"от {format_population(min_pop)}")
    if not send_map(bot, manager, message.chat.id, cities,
                    f"{country}: население {rng} ({len(cities)} шт.)"):
        bot.send_message(message.chat.id, "Не удалось создать карту.")


@bot.message_handler(commands=['weather'])
def handle_weather(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id,
                         "Укажи город: /weather Москва\n"
                         "Несколько городов через запятую: /weather Москва, Париж")
        return

    city_names = [c.strip() for c in parts[1].split(',') if c.strip()][:5]
    for city_name in city_names:
        if not manager.get_coordinates(city_name):
            bot.send_message(message.chat.id,
                             f"Город {city_name} не найден, пропускаю.")
            continue
        text = manager.get_weather(city_name)
        if text:
            bot.send_message(message.chat.id, text)
        else:
            bot.send_message(message.chat.id,
                             f"Не удалось получить погоду для {city_name}.")


@bot.message_handler(commands=['time'])
def handle_time(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id,
                         "Укажи город: /time Токио\n"
                         "Несколько городов через запятую: /time Токио, Париж")
        return

    city_names = [c.strip() for c in parts[1].split(',') if c.strip()][:10]
    for city_name in city_names:
        if not manager.get_coordinates(city_name):
            bot.send_message(message.chat.id,
                             f"Город {city_name} не найден, пропускаю.")
            continue
        text = manager.get_time(city_name)
        if text:
            bot.send_message(message.chat.id, text)
        else:
            bot.send_message(message.chat.id,
                             f"Не удалось получить время для {city_name}.")


if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling()
