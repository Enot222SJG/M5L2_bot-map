import sqlite3
from config import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs


class DB_Map():
    def __init__(self, database):
        self.database = database
    
    def create_user_table(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users_cities (
                                user_id INTEGER,
                                city_id TEXT,
                                FOREIGN KEY(city_id) REFERENCES cities(id)
                            )''')
            conn.commit()

    def add_city(self, user_id, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM cities WHERE city=?", (city_name,))
            city_data = cursor.fetchone()
            if city_data:
                city_id = city_data[0]  
                conn.execute('INSERT INTO users_cities VALUES (?, ?)', (user_id, city_id))
                conn.commit()
                return 1
            else:
                return 0

            
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
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT lat, lng
                            FROM cities  
                            WHERE city = ?''', (city_name,))
            coordinates = cursor.fetchone()
            return coordinates

    def create_grapf(self, path, cities):
        """Создаёт карту с отмеченными городами и сохраняет в файл."""
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

        fig = plt.figure(figsize=(10, 6))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_global()
        ax.coastlines()
        ax.gridlines(draw_labels=True)

        # Отмечаем города красными точками
        ax.scatter(longitudes, latitudes, color='red', s=60,
                   zorder=5, transform=ccrs.PlateCarree())

        # Подписываем каждый город
        for lon, lat, name in zip(longitudes, latitudes, labels):
            ax.text(lon + 1, lat + 1, name, fontsize=8,
                    transform=ccrs.PlateCarree())

        plt.title('Карта городов')
        plt.savefig(path, bbox_inches='tight', dpi=150)
        plt.close(fig)
        return True
        
    def draw_distance(self, city1, city2):
        pass


if __name__ == "__main__":
    
    m = DB_Map(DATABASE)
    m.create_user_table()
