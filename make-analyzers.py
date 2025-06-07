#!/usr/bin/env python3
# -*- coding: utf8 -*-
import glob
import os
import re
import sqlite3
import yaml
from xml.dom import minidom
from typing import List


PATH = os.path.dirname(__file__)
PATH_OF_GIT_REPO = "{}/../".format(PATH)
CONFIG_FILE = "{}/../_config.yml".format(PATH)
PATH_OF_SITE_POSTS = "{}/../_posts/".format(PATH)
PATH_OF_SITE_CAPTURES = "{}/../_captures/".format(PATH)
PATH_OF_WATCH_CAPTURES = "{}/../_watches/".format(PATH)
PATH_OF_ANALYZERS = "{}/../_data/".format(PATH)
PATH_OF_STATIONS = "{}/../_stations/".format(PATH)


def organize_captures(stations_captures):
    def populate_tables(captures_list: List):
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

    captures_organized = []

    for capture in stations_captures:
        base = re.findall("\w{3,5}\d{1,2}.+P\.jpg$", capture)
        capture_spliced = base[0].split('/')
        station = capture_spliced[0]
        capture_date = capture_spliced[3]
        post = (capture_date, station, base[0], capture)

        captures_organized.append(post)

    populate_tables(captures_organized)


def generate_analyzers():
    connection_cursor = connection.cursor()
    connection_cursor.execute("""
    SELECT night_start, station
    FROM captures
    GROUP BY night_start, station
    """)

    for data in connection_cursor.fetchall():
        night_start = str(data[0])
        station = str(data[1])
        capture_filename = PATH_OF_ANALYZERS + "analyzers.yaml"

        connection_cursor.execute("""
            SELECT id, night_start, station, files, files_full_path
            FROM captures
            WHERE night_start = ?
            AND station = ?
            ORDER BY station
            """, (night_start, station))

        for capture in connection_cursor.fetchall():
            file = capture[4].replace('P.jpg', 'A.XML')

            if not os.path.exists(file):
                continue

            try:
                xmldoc = minidom.parse(file)
                itemlist = xmldoc.getElementsByTagName('ua2_object')
                classe = itemlist[0].attributes['class'].value
                magnitude = itemlist[0].attributes['mag'].value
                duration = itemlist[0].attributes['sec'].value
                latitude_start = itemlist[0].attributes['lat1'].value
                latitude_final = itemlist[0].attributes['lat2'].value
                longitude_start = itemlist[0].attributes['lng1'].value
                longitude_final = itemlist[0].attributes['lng2'].value
                velocity = itemlist[0].attributes['Vo'].value
                azimute_start = itemlist[0].attributes['az1'].value
                azimute_final = itemlist[0].attributes['az2'].value
                elevation_start = itemlist[0].attributes['ev1'].value
                elevation_final = itemlist[0].attributes['ev2'].value
                altitude_start = itemlist[0].attributes['h1'].value
                altitude_final = itemlist[0].attributes['h2'].value
            except IndexError:
                classe = "__unknown__"
                magnitude = velocity = duration = "__unknown__"
                latitude_start = latitude_final = "__unknown__"
                longitude_start = longitude_final = "__unknown__"
                azimute_start = azimute_final = "__unknown__"
                elevation_start = elevation_final = "__unknown__"
                altitude_start = altitude_final = "__unknown__"
            except Exception:
                classe = magnitude = duration = velocity = "__none__"
                latitude_start = latitude_final = "__none__"
                longitude_start = longitude_final = "__none__"
                azimute_start = azimute_final = "__none__"
                elevation_start = elevation_final = "__none__"
                altitude_start = altitude_final = "__none__"

            base = re.findall("\w{3}\d{1,2}.+", capture[3])

            filehandle = open(capture_filename, "a")
            filehandle.write("{}:\n".format(base[0]))
            filehandle.write("  station: {}\n".format(station))
            filehandle.write("  class: {}\n".format(classe))
            filehandle.write("  magnitude: {}\n".format(magnitude))
            filehandle.write("  duration: {}\n".format(duration))
            filehandle.write("  latitude_start: {}\n".format(latitude_start))
            filehandle.write("  longitude_start: {}\n".format(longitude_start))
            filehandle.write("  latitude_final: {}\n".format(latitude_final))
            filehandle.write("  longitude_final: {}\n".format(longitude_final))
            filehandle.write("  velocity: {}\n".format(velocity))
            filehandle.write("  azimute_start: {}\n".format(azimute_start))
            filehandle.write("  azimute_final: {}\n".format(azimute_final))
            filehandle.write("  elevation_start: {}\n".format(elevation_start))
            filehandle.write("  elevation_final: {}\n".format(elevation_final))
            filehandle.write("  altitude_start: {}\n".format(altitude_start))
            filehandle.write("  altitude_final: {}\n".format(altitude_final))
            filehandle.close()


def get_matching_captures(captures_dir: list):
    result = []

    for directory in captures_dir:
        files = glob.glob("{}/**/*P.jpg".format(directory), recursive=True)

        result.extend(files)

    return fix_path_delimiter(result)


def fix_path_delimiter(captures_list: list):
    result = []

    for path in captures_list:
        path_fixed = path.replace("\\", "/")

        result.append(path_fixed)

    return result


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


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
    organize_captures(captures)

    print("- Creating analyzers")
    generate_analyzers()

    print("- Closing database connection")
    connection.close()

    print("- Done :)")
