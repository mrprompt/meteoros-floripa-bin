#!/usr/bin/env python3
# -*- coding: utf8 -*-
import glob
import os
import sqlite3
import yaml
from typing import List, Any, LiteralString


PATH = os.path.dirname(__file__)
PATH_OF_STATS = "{}/..".format(PATH)
CONFIG_FILE = "{}/../_config.yml".format(PATH)


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def get_matching_captures(captures_dir: List[LiteralString]) -> List[Any]:
    result = []

    for directory in captures_dir:
        os.chdir(directory)

        files = glob.glob("**/*P.jpg", recursive=True)

        result.extend(files)

    os.chdir(PATH)

    return result


def organize_captures(stations_captures: List) -> List:
    """
    Organize captures to be inserted into database with
    correct params organized into a tuple.

    :param stations_captures: The array all captures
    :returns: List
    """
    captures_organized = []

    for capture in stations_captures:
        capture_spliced = capture.split('/')
        station = capture_spliced[0]
        capture_date = capture_spliced[2]
        post = (capture_date, station, capture)

        captures_organized.append(post)

    return captures_organized


def populate_tables(connection: object, captures_list: List) -> bool:
    """
    Insert posts into table

    :param connection: The database connection
    :param captures_list: Array of posts
    :returns: bool
    """
    connection_cursor = connection.cursor()

    connection_cursor.execute("""
    CREATE TABLE IF NOT EXISTS captures (
        id INTEGER  NOT NULL PRIMARY KEY AUTOINCREMENT,
        capture_month VARCHAR(6) NOT NULL,
        station VARCHAR(20) NOT NULL,
        files TEXT
    );
    """)

    connection_cursor.executemany("INSERT INTO captures (capture_month, station, files) VALUES (?, ?, ?)", captures_list)

    connection.commit()

    return True


def generate_stats(connection: object) -> bool:
    """
    Generate captures collections and pages from every station captures.

    :param connection: The database connection
    :return: bool
    """
    connection_cursor = connection.cursor()
    connection_cursor.execute("""
    SELECT COUNT(files) AS captures, capture_month, station 
    FROM captures 
    GROUP BY capture_month, station
    ORDER BY station, capture_month
    """)

    captures_stats_filename = "{}/estatisticas.html".format(PATH_OF_STATS)
    filehandle = open(captures_stats_filename, "w+")
    filehandle.write("---\n")
    filehandle.write("layout: stats\n")
    filehandle.write("title: Estat&iacute;sticas de Capturas\n")
    filehandle.write("permalink: estatisticas\n")
    filehandle.write("capturas: \n")

    for data in connection_cursor.fetchall():
        captures = str(data[0])
        month_and_year = str(data[1])
        capture_year = str(month_and_year[0:4])
        capture_month = str(month_and_year[4:6])
        station = str(data[2])

        filehandle.write("  - station: {}\n"
                         "    month: {}\n"
                         "    year: {}\n"
                         "    captures: {}\n".format(station, capture_month, capture_year, captures))

    filehandle.write("---\n")
    filehandle.close()

    return True


if __name__ == '__main__':
    print("- Connecting to database")
    connection = sqlite3.connect(':memory:')

    print("- Loading site configuration")
    config = load_config()
    captures_dir = config['build']['captures']

    print('- Reading captures')
    captures = get_matching_captures(captures_dir)

    if len(captures) == 0:
        print("- Nothing to do")
        exit(0)

    print("- Organizing captures")
    posts = organize_captures(captures)

    print("- Creating temporary table and populating...")
    populate_tables(connection, posts)

    print("- Creating stats")
    generate_stats(connection)

    print("- Closing database connection")
    connection.close()

    print("- Done :)")
