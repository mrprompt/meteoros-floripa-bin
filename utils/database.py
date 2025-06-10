import sqlite3
import os
from sqlite3 import Connection as Connection

DatabaseFile = 'capturas.db'


def get_connection() -> Connection:
    return sqlite3.connect(DatabaseFile)


def close_connection() -> None:
    os.remove(DatabaseFile)
