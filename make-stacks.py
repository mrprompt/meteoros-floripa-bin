#!/usr/bin/env python3
# -*- coding: utf8 -*-
import glob
import os
import yaml
from typing import List
from PIL import ImageChops, Image
from utils import captures, database, config


PATH = os.path.dirname(__file__)
PATH_OF_GIT_REPO = "{}/../".format(PATH)
CONFIG_FILE = "{}/../_config.yml".format(PATH)
PATH_OF_SITE_POSTS = "{}/../_posts/".format(PATH)
PATH_OF_SITE_CAPTURES = "{}/../_captures/".format(PATH)
PATH_OF_WATCH_CAPTURES = "{}/../_watches/".format(PATH)
PATH_OF_ANALYZERS = "{}/../_data/".format(PATH)
PATH_OF_STATIONS = "{}/../_stations/".format(PATH)


def generate_stacks():
    connection = database.get_connection()
    connection_cursor = connection.cursor()
    connection_cursor.execute("""
    SELECT night_start, station
    FROM captures
    GROUP BY night_start, station
    """)

    for data in connection_cursor.fetchall():
        stack: list[str] = []
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

        captures.stack(stack, "{}/stack.jpg".format(stack_output_dir))


if __name__ == '__main__':
    print("- Loading site configuration")
    configuration = config.load_config()

    print("- Reading captures")
    files_captures = captures.get_captures(configuration['captures'], configuration['days'])

    if len(files_captures) == 0:
        print("- Nothing to do")
        print("- Closing database connection")

        database.close_connection()

        exit(0)

    print("- Creating stacks")
    generate_stacks()

    print("- Closing database connection")
    database.close_connection()

    print("- Done :)")
