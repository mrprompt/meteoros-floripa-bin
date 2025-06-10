#!/usr/bin/env python3
# -*- coding: utf8 -*-
import os
import re
import datetime

from utils import captures, config,  database
from xml.dom import minidom
from git import Repo


PATH_OF_ANALYZERS = "/_data/"


def generate_analyzers():
    connection = database.get_connection()
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

            base = re.findall(r"\w{3}\d{1,2}.+", capture[3])

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


def git_push(path_of_git_repo: str):
    try:
        os.chdir(path_of_git_repo)

        repo = Repo(path_of_git_repo)
        repo.git.add(update=True)
        repo.git.add(path_of_git_repo + PATH_OF_ANALYZERS)
        
        repo.index.commit("Update analyzers")

        origin = repo.remote(name='origin')
        origin.push()
    except:
        print("- Some error occurred while pushing the code")

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

    print("- Creating analyzers")
    generate_analyzers()

    print("- Push to git")
    git_push(configuration['output']['base'])

    print("- Closing database connection")
    database.close_connection()

    print("- Done :)")
