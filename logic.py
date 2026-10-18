import sqlite3
from config import *
import warnings
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.io import DownloadWarning
from googletrans import Translator
import requests

warnings.filterwarnings('ignore', category=DownloadWarning)
warnings.filterwarnings('ignore', message='facecolor will have no effect')

RU_COUNTRIES = {
    'россия': 'Russia', 'япония': 'Japan', 'франция': 'France',
    'германия': 'Germany', 'китай': 'China', 'индия': 'India',
    'бразилия': 'Brazil', 'сша': 'United States', 'америка': 'United States',
    'соединённые штаты': 'United States', 'соединенные штаты': 'United States',
    'великобритания': 'United Kingdom', 'англия': 'United Kingdom',
    'италия': 'Italy', 'испания': 'Spain', 'украина': 'Ukraine',
    'беларусь': 'Belarus', 'казахстан': 'Kazakhstan', 'польша': 'Poland',
    'канада': 'Canada', 'мексика': 'Mexico', 'египет': 'Egypt',
    'турция': 'Turkey', 'греция': 'Greece', 'нидерланды': 'Netherlands',
    'швеция': 'Sweden', 'норвегия': 'Norway', 'финляндия': 'Finland',
    'португалия': 'Portugal', 'австралия': 'Australia', 'аргентина': 'Argentina',
    'южная корея': 'South Korea', 'корея': 'South Korea', 'индонезия': 'Indonesia',
    'тайвань': 'Taiwan', 'тайланд': 'Thailand', 'вьетнам': 'Vietnam',
    'швейцария': 'Switzerland', 'австрия': 'Austria', 'чехия': 'Czechia',
    'румыния': 'Romania', 'сербия': 'Serbia', 'израиль': 'Israel',
    'иран': 'Iran', 'ирак': 'Iraq', 'колумбия': 'Colombia', 'чили': 'Chile',
    'перу': 'Peru', 'венгрия': 'Hungary', 'дания': 'Denmark', 'ирландия': 'Ireland',
    'бельгия': 'Belgium', 'новая зеландия': 'New Zealand', 'южно-африканская республика': 'South Africa',
    'юар': 'South Africa', 'марокко': 'Morocco', 'нигерия': 'Nigeria',
    'пакистан': 'Pakistan', 'филиппины': 'Philippines', 'малайзия': 'Malaysia',
    'сингапур': 'Singapore', 'катар': 'Qatar',
    'оаэ': 'United Arab Emirates', 'объединённые арабские эмираты': 'United Arab Emirates',
    'объединенные арабские эмираты': 'United Arab Emirates', 'саудовская аравия': 'Saudi Arabia',
    'куба': 'Cuba', 'венесуэла': 'Venezuela', 'эквадор': 'Ecuador',
    'боливия': 'Bolivia', 'уругвай': 'Uruguay',
    'парагвай': 'Paraguay',
}

WEATHER_SYMBOLS = {
    'clearsky': 'Ясно', 'fair': 'Малооблачно', 'partlycloudy': 'Переменная облачность',
    'cloudy': 'Пасмурно', 'fog': 'Туман', 'lightrain': 'Небольшой дождь',
    'rain': 'Дождь', 'heavyrain': 'Сильный дождь', 'lightshowers': 'Небольшой ливень',
    'showers': 'Ливень', 'heavyshowers': 'Сильный ливень', 'sleet': 'Мокрый снег',
    'lightsleet': 'Лёгкий мокрый снег', 'heavysleet': 'Сильный мокрый снег',
    'lightsnow': 'Небольшой снег',
    'snow': 'Снег', 'heavysnow': 'Сильный снег', 'lightsnowshowers': 'Небольшой снегопад',
    'snowshowers': 'Снегопад', 'heavysnowshowers': 'Сильный снегопад',
    'thunderstorm': 'Гроза', 'thundershower': 'Гроза с дождём',
    'thundershowerwithhail': 'Гроза с градом', 'lightrainshowers': 'Небольшой ливень',
    'rainshowers': 'Ливень', 'heavyrainshowers': 'Сильный ливень',
}


class DB_Map():
    def __init__(self, database):
        self.database = database
        self.translator = Translator()

    def create_user_table(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users_cities (
                                user_id INTEGER,
                                city_id TEXT,
                                FOREIGN KEY(city_id) REFERENCES cities(id)
                            )''')
            # Таблица для хранения настроек пользователя (цвет маркера)
            conn.execute('''CREATE TABLE IF NOT EXISTS user_settings (
                                user_id INTEGER PRIMARY KEY,
                                marker_color TEXT DEFAULT 'red'
                            )''')
            conn.commit()

    def set_color(self, user_id, color):
        """Сохраняет выбранный цвет маркера для пользователя."""
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''INSERT INTO user_settings (user_id, marker_color)
                            VALUES (?, ?)
                            ON CONFLICT(user_id) DO UPDATE SET marker_color=?''',
                         (user_id, color, color))
            conn.commit()

    def get_color(self, user_id):
        """Возвращает цвет маркера пользователя (по умолчанию red)."""
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('SELECT marker_color FROM user_settings WHERE user_id=?', (user_id,))
            row = cursor.fetchone()
            return row[0] if row else 'red'

    def translate_city(self, city_name):
        """Переводит название города на английский, если оно на русском."""
        # Проверяем, есть ли кириллица
        if any('а' <= c.lower() <= 'я' or c.lower() == 'ё' for c in city_name):
            try:
                result = self.translator.translate(city_name, src='ru', dest='en')
                return result.text.strip()
            except Exception:
                return city_name
        return city_name

    def add_city(self, user_id, city_name):
        city_name_en = self.translate_city(city_name)
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM cities WHERE city=?", (city_name_en,))
            city_data = cursor.fetchone()
            if city_data:
                city_id = city_data[0]
                conn.execute('INSERT INTO users_cities VALUES (?, ?)', (user_id, city_id))
                conn.commit()
                return city_name_en
            else:
                return None

    def select_cities(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cities.city 
                            FROM users_cities  
                            JOIN cities ON users_cities.city_id = cities.id
                            WHERE users_cities.user_id = ?''', (user_id,))
            cities = [row[0] for row in cursor.fetchall()]
            return cities

    def get_coordinates(self, city_name):
        city_name_en = self.translate_city(city_name)
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT lat, lng
                            FROM cities  
                            WHERE city = ?''', (city_name_en,))
            coordinates = cursor.fetchone()
            return coordinates

    def _translate_country(self, country_name):
        """Переводит название страны на английский."""
        key = country_name.strip().lower()
        if key in RU_COUNTRIES:
            return RU_COUNTRIES[key]
        if any('а' <= c.lower() <= 'я' or c.lower() == 'ё' for c in country_name):
            try:
                result = self.translator.translate(country_name, src='ru', dest='en')
                return result.text.strip()
            except Exception:
                return country_name
        return country_name

    def get_countries(self):
        """Возвращает список стран из базы (английские названия)."""
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT country, COUNT(*) AS cnt
                            FROM cities GROUP BY country
                            ORDER BY country''')
            return cursor.fetchall()

    def cities_by_country(self, country, limit=30):
        """Возвращает города конкретной страны (по умолчанию топ-30 по населению)."""
        country_en = self._translate_country(country)
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT city FROM cities
                            WHERE LOWER(country) = LOWER(?)
                            ORDER BY population DESC LIMIT ?''',
                           (country_en, limit))
            return [row[0] for row in cursor.fetchall()]

    def cities_by_population(self, min_pop, max_pop=None, limit=30):
        """Возвращает города с населением в указанном диапазоне."""
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            if max_pop is None:
                cursor.execute('''SELECT city FROM cities
                                WHERE population >= ?
                                ORDER BY population DESC LIMIT ?''',
                               (min_pop, limit))
            else:
                cursor.execute('''SELECT city FROM cities
                                WHERE population BETWEEN ? AND ?
                                ORDER BY population DESC LIMIT ?''',
                               (min_pop, max_pop, limit))
            return [row[0] for row in cursor.fetchall()]

    def cities_by_country_and_population(self, country, min_pop, max_pop=None, limit=30):
        """Возвращает города страны с населением в указанном диапазоне."""
        country_en = self._translate_country(country)
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            if max_pop is None:
                cursor.execute('''SELECT city FROM cities
                                WHERE LOWER(country) = LOWER(?) AND population >= ?
                                ORDER BY population DESC LIMIT ?''',
                               (country_en, min_pop, limit))
            else:
                cursor.execute('''SELECT city FROM cities
                                WHERE LOWER(country) = LOWER(?)
                                  AND population BETWEEN ? AND ?
                                ORDER BY population DESC LIMIT ?''',
                               (country_en, min_pop, max_pop, limit))
            return [row[0] for row in cursor.fetchall()]

    def _city_api_data(self, city_name):
        """Возвращает координаты города из базы или None."""
        coords = self.get_coordinates(city_name)
        if not coords or coords[0] is None or coords[1] is None:
            return None
        return {'lat': coords[0], 'lng': coords[1]}

    def get_weather(self, city_name):
        """Возвращает текст с текущей погодой в городе (met.no) или None."""
        info = self._city_api_data(city_name)
        if not info:
            return None
        try:
            response = requests.get(
                'https://api.met.no/weatherapi/locationforecast/2.0/compact',
                params={'lat': info['lat'], 'lon': info['lng']},
                headers={'User-Agent': 'M5L2-city-map-bot'}, timeout=10)
            response.raise_for_status()
            timeseries = response.json()['properties']['timeseries']
        except Exception:
            return None

        details = timeseries[0]['data']['instant']['details']
        temp = details.get('air_temperature')
        wind = details.get('wind_speed')

        description = None
        for moment in timeseries[:6]:
            for period in ('next_1_hours', 'next_6_hours'):
                symbol = ((moment['data'].get(period) or {})
                          .get('summary', {}).get('symbol_code'))
                if symbol:
                    base = symbol.split('_')[0]
                    description = WEATHER_SYMBOLS.get(base, symbol)
                    break
            if description:
                break

        lines = [f"Погода в городе {city_name}:"]
        if description:
            lines.append(description)
        if temp is not None:
            lines.append(f"Температура: {temp:.0f} °C")
        if wind is not None:
            lines.append(f"Ветер: {wind:.0f} км/ч")
        return "\n".join(lines)

    def get_time(self, city_name):
        """Возвращает текущее местное время в городе (timeapi.io) или None."""
        info = self._city_api_data(city_name)
        if not info:
            return None
        try:
            response = requests.get(
                'https://timeapi.io/api/Time/current/coordinate',
                params={'latitude': info['lat'], 'longitude': info['lng']},
                timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return None

        local = data['dateTime'][:19].replace('T', ' ')
        tz = data.get('timeZone', '').split('/')[-1].replace('_', ' ')
        return (f"Время в городе {city_name}: {local}"
                + (f" ({tz})" if tz else ''))

    def create_grapf(self, path, cities, marker_color='red'):
        """Создаёт красивую карту с городами и географическими объектами."""
        latitudes = []
        longitudes = []
        labels = []

        for city in cities:
            coords = self.get_coordinates(city)
            if coords:
                lat, lng = coords
                if lat is not None and lng is not None:
                    latitudes.append(lat)
                    longitudes.append(lng)
                    labels.append(city)

        if not latitudes:
            return False

        fig = plt.figure(figsize=(12, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_global()

        lat_span = max(latitudes) - min(latitudes)
        lon_span = max(longitudes) - min(longitudes)
        if len(latitudes) > 1 and lat_span < 60 and lon_span < 80:
            pad = max(lat_span, lon_span, 3) * 0.3 + 1
            ax.set_extent([min(longitudes) - pad, max(longitudes) + pad,
                           min(latitudes) - pad, max(latitudes) + pad],
                          crs=ccrs.PlateCarree())

        # Заливка океана и континентов
        ax.add_feature(cfeature.OCEAN, color='lightblue')
        ax.add_feature(cfeature.LAND, color='lightgreen')

        # Географические объекты
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
        ax.add_feature(cfeature.RIVERS, color='blue', linewidth=0.3)
        ax.add_feature(cfeature.LAKES, color='lightblue')

        ax.gridlines(draw_labels=True, linewidth=0.3, alpha=0.5)

        marker_size = 80 if len(latitudes) <= 15 else 30
        label_size = 8 if len(latitudes) <= 15 else 5
        offset = max(lat_span, lon_span) * 0.02 + 0.5

        # Маркеры городов
        ax.scatter(longitudes, latitudes, color=marker_color, s=marker_size,
                   edgecolors='black', linewidths=0.5, zorder=5,
                   transform=ccrs.PlateCarree())

        # Подписи
        for lon, lat, name in zip(longitudes, latitudes, labels):
            ax.text(lon + offset, lat + offset, name, fontsize=label_size,
                    fontweight='bold', transform=ccrs.PlateCarree())

        plt.title(f'Карта городов ({len(latitudes)} шт.)', fontsize=14)
        plt.savefig(path, bbox_inches='tight', dpi=150)
        plt.close(fig)
        return True


def preload_map_data():
    """Заранее скачивает картографические данные Natural Earth в кэш cartopy."""
    try:
        for feature in (cfeature.OCEAN, cfeature.LAND, cfeature.COASTLINE,
                        cfeature.BORDERS, cfeature.RIVERS, cfeature.LAKES):
            list(feature.geometries())
    except Exception as e:
        print(f"Не удалось скачать картографические данные: {e}")


if __name__ == "__main__":
    m = DB_Map(DATABASE)
    m.create_user_table()
