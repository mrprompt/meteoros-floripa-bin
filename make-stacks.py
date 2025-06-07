#!/usr/bin/env python3
# -*- coding: utf8 -*-
import glob
import os
import re
import sqlite3
import yaml
from typing import List
from PIL import ImageChops, Image


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


def generate_stacks():
    def stack_captures(data, output_file):
        try:
            stack = Image.open(data[0])

            for i in range(1, len(data)):
                current_image = Image.open(data[i])
                stack = ImageChops.lighter(stack, current_image)

            stack.save(output_file, "JPEG")
        except:
            pass

    connection_cursor = connection.cursor()
    connection_cursor.execute("""
    SELECT night_start, station
    FROM captures
    GROUP BY night_start, station
    """)

    for data in connection_cursor.fetchall():
        stack = []
        stack_output_dir = "./"
        night_start = str(data[0])
        station = str(data[1])

        connection_cursor.execute("""
            SELECT id, night_start, station, files, files_full_path
            FROM captures
            WHERE night_start = ?
            AND station = ?
            ORDER BY station
            """, (night_start, station))

        for capture in connection_cursor.fetchall():
            stack.append(capture[4])
            stack_output_dir = os.path.dirname(capture[4])

        stack_captures(stack, "{}/stack.jpg".format(stack_output_dir))


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

    print("- Creating stacks")
    generate_stacks()

    print("- Closing database connection")
    connection.close()

    print("- Done :)")
