import sqlite3
from typing import List, Tuple

CaptureRecord = Tuple[str, str, str, str]


def get_connection():
    return sqlite3.connect('capturas.db')


def populate_tables(captures_list: List[CaptureRecord]) -> None:
    connection = get_connection()
    connection_cursor = connection.cursor()
    connection_cursor.execute("""
    CREATE TABLE IF NOT EXISTS captures (
        id INTEGER  NOT NULL PRIMARY KEY AUTOINCREMENT,
        night_start DATE NOT NULL,
        station VARCHAR(20) NOT NULL,
        files TEXT,
        files_full_path TEXT
    );
    """)

    connection_cursor.executemany("""
    INSERT INTO captures (night_start, station, files, files_full_path)
    VALUES (?, ?, ?, ?)
    """, captures_list)

    connection.commit()