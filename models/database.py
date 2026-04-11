import sqlite3
import os


DB_NAME = "digitalization.db"


def create_database():

    # если база уже существует — удаляем её
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # таблица федеральных округов
    cursor.execute("""
    CREATE TABLE federal_districts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    # таблица регионов
    cursor.execute("""
    CREATE TABLE regions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        federal_district_id INTEGER,
        FOREIGN KEY (federal_district_id) REFERENCES federal_districts(id)
    )
    """)

    # таблица факторов
    cursor.execute("""
    CREATE TABLE indicators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    # таблица значений факторов
    cursor.execute("""
    CREATE TABLE values_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        territory_type TEXT,
        territory_id INTEGER,
        indicator_id INTEGER,
        year INTEGER,
        value REAL
    )
    """)

    conn.commit()
    conn.close()