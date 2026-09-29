import sqlite3
from sqlite3 import Connection as Connection

DatabaseFile = 'capturas.db'


def get_connection() -> Connection:
    return sqlite3.connect(DatabaseFile)


def close_connection(connection: Connection) -> None:
    connection.close()
