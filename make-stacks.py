#!/usr/bin/env python3
# -*- coding: utf8 -*-
import glob
import os
import yaml
from typing import List
from PIL import ImageChops, Image
from utils import captures, database, config
from sqlite3 import Connection


PATH = os.path.dirname(__file__)
CONFIG_FILE = "{}/_config.yml".format(PATH)
PATH_OF_SITE_CAPTURES = "{}/../_captures/".format(PATH)


def generate_stacks(connection: Connection):
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

    connection = database.get_connection()
    try:
        print("- Reading captures")
        files_captures = captures.get_captures(connection, configuration['captures'], configuration['days'])

        if len(files_captures) == 0:
            print("- Nothing to do")
        else:
            print("- Creating stacks")
            generate_stacks(connection)
            print("- Done :)")
    finally:
        print("- Closing database connection")
        database.close_connection(connection)
