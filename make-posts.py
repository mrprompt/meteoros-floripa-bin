#!/usr/bin/env python3
# -*- coding: utf8 -*-
import os
import re
import datetime

from utils import captures, config,  database, video
from xml.dom import minidom
from git import Repo


PATH_OF_SITE_POSTS = "/_posts/"
PATH_OF_SITE_CAPTURES = "/_captures/"
PATH_OF_WATCH_CAPTURES = "/_watches/"
PATH_OF_ANALYZERS = "/_data/"
PATH_OF_STATIONS = "/_stations/"


def generate_captures(output_dir: str = "./"):
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
        capture_filename = "{}{}{}_{}.md".format(output_dir, PATH_OF_SITE_CAPTURES, station, night_start)

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

            file = capture[3]

            capture_spliced = file.split('/')
            capture_base_filename = capture_spliced[-1]
            capture_data_spliced = capture_base_filename.split('_')

            capture_date = capture_data_spliced[0]
            capture_day = capture_date[7:9]
            capture_month = capture_date[5:7]
            capture_year = capture_date[1:5]

            capture_time = capture_data_spliced[1]
            capture_hour = capture_time[0:2]
            capture_minute = capture_time[2:4]
            capture_second = capture_time[4:6]

            if not os.path.exists(capture_filename):
                filehandle = open(capture_filename, "w+")
                filehandle.write("---\n")
                filehandle.write("layout: capture\n")
                filehandle.write("label: {}\n".format(night_start))
                filehandle.write("title: Capturas da esta&ccedil;&atilde;o {}\n".format(station))
                filehandle.write("station: {}\n".format(station))
                filehandle.write("date: {}-{}-{} {}:{}:{}\n".format(capture_year, capture_month, capture_day, capture_hour, capture_minute, capture_second))
                filehandle.write("preview: {}/stack.jpg\n".format(os.path.dirname(file)))
                filehandle.write("capturas:\n")
            else:
                filehandle = open(capture_filename, "a")

            filehandle.write("  - imagem: {}\n".format(file))
            filehandle.close()

        filehandle = open(capture_filename, "a")
        filehandle.write("---\n")
        filehandle.close()

        captures.stack(stack, "{}/stack.jpg".format(stack_output_dir))


def generate_posts(output_dir: str = "./"):
    connection = database.get_connection()
    connection_cursor = connection.cursor()
    connection_cursor.execute("""
    SELECT night_start, files
    FROM captures
    GROUP BY night_start
    """)

    for data in connection_cursor.fetchall():
        night_start = str(data[0])
        day = str(night_start[6:8])
        month = str(night_start[4:6])
        year = str(night_start[0:4])
        file_preview = str(data[1])
        post_filename = "{}{}{}-{}-{}-captures.md".format(output_dir, PATH_OF_SITE_POSTS, year, month, day)

        filehandle = open(post_filename, "w+")
        filehandle.write("---\n")
        filehandle.write("layout: post\n")
        filehandle.write("title: {}/{}/{}\n".format(day, month, year))
        filehandle.write("date: {}-{}-{} 10:00:00\n".format(year, month, day))
        filehandle.write("preview: {}/stack.jpg\n".format(os.path.dirname(file_preview)))
        filehandle.write("---\n")
        filehandle.close()


def generate_watches(output_dir: str = "./"):
    connection = database.get_connection()
    connection_cursor = connection.cursor()
    connection_cursor.execute("""
    SELECT night_start, station, files, files_full_path
    FROM captures
    """)

    for data in connection_cursor.fetchall():
        station = str(data[1])
        file = str(data[2])
        capture_spliced = file.split('/')
        capture_base_filename = capture_spliced[-1]
        capture_base_filename_spliced = capture_base_filename.split('_')
        day = capture_base_filename_spliced[0][7:9]
        month = capture_base_filename_spliced[0][5:7]
        year = capture_base_filename_spliced[0][1:5]
        hour = capture_base_filename_spliced[1][0:2]
        minute = capture_base_filename_spliced[1][2:4]
        second = capture_base_filename_spliced[1][4:6]

        filehandle = open("{}{}{}.md".format(output_dir, PATH_OF_WATCH_CAPTURES, capture_base_filename.replace('P.jpg', '')), "w+")
        filehandle.write("---\n")
        filehandle.write("layout: watch\n")
        filehandle.write("title: {} - {}/{}/{} - {}\n".format(station, day, month, year, capture_base_filename.replace('P.jpg', 'T.jpg')))
        filehandle.write("date: {}-{}-{} {}:{}:{}\n".format(year, month, day, hour, minute, second))
        filehandle.write("permalink: /{}/{}/{}/watch/{}\n".format(year, month, day, capture_base_filename.replace('P.jpg', '')))
        filehandle.write("capture: {}\n".format(file.replace('P.jpg', 'T.jpg')))
        filehandle.write("---\n")
        filehandle.close()


def generate_analyzers(output_dir: str = "./"):
    connection = database.get_connection()
    connection_cursor = connection.cursor()
    connection_cursor.execute("""
    SELECT night_start, station
    FROM captures
    GROUP BY night_start, station
    """)
    
    analyzers_file = output_dir + "/" + PATH_OF_ANALYZERS + "analyzers.yaml"

    for data in connection_cursor.fetchall():
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

            filehandle = open(analyzers_file, "a")
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


def generate_videos(output_dir: str = "./"):
    connection = database.get_connection()
    connection_cursor = connection.cursor()
    connection_cursor.execute("""
    SELECT files_full_path
    FROM captures
    """)

    for data in connection_cursor.fetchall():
        video_input = (data[0].replace('P.jpg', '.avi'))
        video_output = output_dir + "/" + os.path.basename(data[0].replace('P.jpg', '.mp4'))

        video.converter(video_input, video_output)


def git_push(path_of_git_repo: str):
    try:
        today = datetime.date.today()

        os.chdir(path_of_git_repo)

        repo = Repo(path_of_git_repo)
        repo.git.add(update=True)
        repo.git.add(path_of_git_repo + PATH_OF_SITE_CAPTURES)
        repo.git.add(path_of_git_repo + PATH_OF_SITE_POSTS)
        repo.git.add(path_of_git_repo + PATH_OF_WATCH_CAPTURES)
        repo.git.add(path_of_git_repo + PATH_OF_ANALYZERS)
        repo.git.add(path_of_git_repo + PATH_OF_STATIONS)
        
        repo.index.commit("Captures of {}".format(today))

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

    print("- Creating captures")
    generate_captures(configuration['output']['base'])

    print("- Creating posts")
    generate_posts(configuration['output']['base'])

    print("- Creating watches")
    generate_watches(configuration['output']['base'])

    print("- Creating analyzers")
    generate_analyzers(configuration['output']['base'])

    print("- Creating videos")
    generate_videos(configuration['storage']['videos'])

    print("- Uploading captures")
    captures.upload_captures(configuration['captures'], configuration['storage']['captures'])

    print("- Push to git")
    git_push(configuration['output']['base'])

    print("- Closing database connection")
    database.close_connection()

    print("- Done :)")
