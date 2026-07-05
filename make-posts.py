#!/usr/bin/env python3
# -*- coding: utf8 -*-
import os
from utils import captures, config,  database
from git import Repo

print("- Loading site configuration")
configuration = config.load_config()


PATH = os.path.dirname(configuration['output']['base'])
PATH_OF_GIT_REPO = "{}/".format(PATH)
CONFIG_FILE = "{}/_config.yml".format(PATH)
PATH_OF_SITE_POSTS = "{}/_posts/".format(PATH)
PATH_OF_SITE_CAPTURES = "{}/_captures/".format(PATH)
PATH_OF_WATCH_CAPTURES = "{}/_watches/".format(PATH)


def generate_posts():
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
        day = str(night_start[6:8])
        month = str(night_start[4:6])
        year = str(night_start[0:4])
        post_filename = PATH_OF_SITE_POSTS + "{}-{}-{}-{}.md".format(year, month, day, station)

        connection_cursor.execute("""
            SELECT id, night_start, station, files, files_full_path
            FROM captures
            WHERE night_start = ?
            AND station = ?
            ORDER BY station
            """, (night_start, station))

        filehandle = open(post_filename, "w")
        filehandle.write("---\n")
        filehandle.write("layout: post\n")
        filehandle.write("title: Capturas da esta&ccedil;&atilde;o {}\n".format(station))
        filehandle.write("date: {}-{}-{} 10:00:00 -0300\n".format(year, month, day))
        filehandle.write("categories: [capturas]\n")
        filehandle.write("tags: [capturas, esta&ccedil;&atilde;o, {}]\n".format(station))
        filehandle.write("station: {}\n".format(station))
        filehandle.write("captures: \n")

        stack_files: list[str] = []
        stack_output_dir = ""

        for capture in connection_cursor.fetchall():
            stack_files.append(capture[4])
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

            filehandle.write("  - image: {}\n".format(file))
            filehandle.write("    date_full: {}-{}-{} {}:{}:{}\n".format(capture_year, capture_month, capture_day,
                                                                         capture_hour, capture_minute, capture_second))

        if stack_files:
            captures.stack(stack_files, "{}/stack.jpg".format(stack_output_dir))
            filehandle.write("preview: {}/stack.jpg\n".format(stack_output_dir))

        filehandle.write("---\n")
        filehandle.close()


def generate_watches():
    connection = database.get_connection()
    connection_cursor = connection.cursor()
    connection_cursor.execute("""
    SELECT files, station
    FROM captures
    """)

    for data in connection_cursor.fetchall():
        file = str(data[0])
        station = str(data[1])
        capture_spliced = file.split('/')
        capture_base_filename = capture_spliced[-1]
        capture_base_filename_spliced = capture_base_filename.split('_')
        day = capture_base_filename_spliced[0][7:9]
        month = capture_base_filename_spliced[0][5:7]
        year = capture_base_filename_spliced[0][1:5]
        hour = capture_base_filename_spliced[1][0:2]
        minute = capture_base_filename_spliced[1][2:4]
        second = capture_base_filename_spliced[1][4:6]
        
        base_name_without_ext = capture_base_filename.replace('P.jpg', '')
        watch_filename = PATH_OF_WATCH_CAPTURES + "{}-{}-{}-watch-{}.md".format(year, month, day, base_name_without_ext)

        filehandle = open(watch_filename, "w")
        filehandle.write("---\n")
        filehandle.write("layout: watch\n")
        filehandle.write("title: Captura da esta&ccedil;&atilde;o {} - {}\n".format(station, base_name_without_ext))
        filehandle.write("date: {}-{}-{} {}:{}:{} -0300\n".format(year, month, day, hour, minute, second))
        filehandle.write("categories: [watches]\n")
        filehandle.write("tags: [watches, esta&ccedil;&atilde;o, {}]\n".format(station))
        filehandle.write("station: {}\n".format(station))
        filehandle.write("permalink: /{}/{}/{}/watch/{}\n".format(year, month, day, base_name_without_ext))
        filehandle.write("capture: {}\n".format(file.replace('P.jpg', 'T.jpg')))
        filehandle.write("---\n")
        filehandle.close()


def git_push(path_of_git_repo: str):
    try:
        os.chdir(path_of_git_repo)

        repo = Repo(path_of_git_repo)
        repo.git.add(update=True)
        repo.git.add(PATH_OF_SITE_POSTS)
        repo.git.add(PATH_OF_SITE_CAPTURES)
        repo.git.add(PATH_OF_WATCH_CAPTURES)
        
        repo.index.commit("Update posts")

        origin = repo.remote(name='origin')
        origin.push()
    except:
        print("- Some error occurred while pushing the code")


if __name__ == '__main__':
    print("- Reading captures")
    files_captures = captures.get_captures(configuration['captures'], configuration['days'])

    if len(files_captures) == 0:
        print("- Nothing to do")
        print("- Closing database connection")

        database.close_connection()

        exit(0)

    print("- Creating posts")
    generate_posts()

    print("- Creating watches")
    generate_watches()

    print("- Uploading captures (Windows only)")
    # captures.upload_captures(configuration['captures'], configuration['storage']['captures'])

    print("- Push to git")
    # git_push(configuration['output']['base'])

    print("- Closing database connection")
    # database.close_connection()

    print("- Done :)")