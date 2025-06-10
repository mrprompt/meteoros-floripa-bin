#!/usr/bin/env python3
# -*- coding: utf8 -*-
from utils import captures, config,  database


def generate_stats(output_dir: str = "./") -> bool:
    """
    Generate captures collections and pages from every station captures.

    :param connection: The database connection
    :return: bool
    """
    connection = database.get_connection()
    connection_cursor = connection.cursor()
    connection_cursor.execute("""
    SELECT COUNT(files) AS captures, capture_month, station 
    FROM captures 
    GROUP BY capture_month, station
    ORDER BY station, capture_month
    """)

    filehandle = open(output_dir + "/estatisticas.html", "w+")
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
    print("- Loading site configuration")
    configuration = config.load_config()

    print("- Reading captures")
    files_captures = captures.get_captures(configuration['captures'], configuration['days'])

    if len(files_captures) == 0:
        print("- Nothing to do")
        print("- Closing database connection")

        database.close_connection()

        exit(0)

    print("- Creating stats")
    generate_stats(configuration['output']['base'])

    print("- Closing database connection")
    database.close_connection()

    print("- Done :)")
