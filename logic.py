import sqlite3
from config import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from googletrans import Translator


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

        # Заливка океана и континентов
        ax.add_feature(cfeature.OCEAN, color='lightblue')
        ax.add_feature(cfeature.LAND, color='lightgreen')

        # Географические объекты
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
        ax.add_feature(cfeature.RIVERS, color='blue', linewidth=0.3)
        ax.add_feature(cfeature.LAKES, color='lightblue')

        ax.gridlines(draw_labels=True, linewidth=0.3, alpha=0.5)

        # Маркеры городов
        ax.scatter(longitudes, latitudes, color=marker_color, s=80,
                   edgecolors='black', linewidths=0.5, zorder=5,
                   transform=ccrs.PlateCarree())

        # Подписи
        for lon, lat, name in zip(longitudes, latitudes, labels):
            ax.text(lon + 1, lat + 1, name, fontsize=8, fontweight='bold',
                    transform=ccrs.PlateCarree())

        plt.title('Карта городов', fontsize=14)
        plt.savefig(path, bbox_inches='tight', dpi=150)
        plt.close(fig)
        return True


if __name__ == "__main__":
    m = DB_Map(DATABASE)
    m.create_user_table()
