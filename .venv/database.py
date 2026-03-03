import sqlite3

DB_NAME = "digitalization.db"

def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS federal_districts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS regions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        federal_district_id INTEGER NOT NULL,
        FOREIGN KEY (federal_district_id) REFERENCES federal_districts(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS indicators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        column_name TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS values_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        territory_type TEXT NOT NULL,
        territory_id INTEGER NOT NULL,
        indicator_id INTEGER NOT NULL,
        year INTEGER NOT NULL,
        value REAL NOT NULL
    );
    """)

    conn.commit()
    conn.close()

