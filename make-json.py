#!/usr/bin/env python3
# -*- coding: utf8 -*-
import os
import re
import datetime
import json

from utils import captures, config,  database, video
from xml.dom import minidom


def generate_captures_data():
    connection = database.get_connection()
    connection_cursor = connection.cursor()
    connection_cursor.execute("""
    SELECT night_start, station
    FROM captures
    GROUP BY night_start, station
    """)

    all_captures_data = []

    for data in connection_cursor.fetchall():
        stack_files: list[str] = []
        night_start = str(data[0])
        station = str(data[1])
        
        connection_cursor.execute("""
            SELECT id, night_start, station, files, files_full_path
            FROM captures
            WHERE night_start = ?
            AND station = ?
            ORDER BY station
            """, (night_start, station))

        capture_items = []
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

            capture_items.append({
                "image": file,
                "date_full": f"{capture_year}-{capture_month}-{capture_day} {capture_hour}:{capture_minute}:{capture_second}"
            })
        
        if stack_files:
            stack_image_path = f"{stack_output_dir}/stack.jpg"
            captures.stack(stack_files, stack_image_path)

            all_captures_data.append({
                "night_start": night_start,
                "station": station,
                "title": f"Capturas da estação {station}",
                "preview": stack_image_path,
                "captures": capture_items
            })
    
    return all_captures_data


def generate_posts_data():
    connection = database.get_connection()
    connection_cursor = connection.cursor()
    connection_cursor.execute("""
    SELECT night_start, files
    FROM captures
    GROUP BY night_start
    """)

    all_posts_data = []

    for data in connection_cursor.fetchall():
        night_start = str(data[0])
        day = str(night_start[6:8])
        month = str(night_start[4:6])
        year = str(night_start[0:4])
        file_preview = str(data[1])
        
        all_posts_data.append({
            "title": f"{day}/{month}/{year}",
            "date": f"{year}-{month}-{day} 10:00:00",
            "preview": f"{os.path.dirname(file_preview)}/stack.jpg"
        })
    
    return all_posts_data


def generate_watches_data():
    connection = database.get_connection()
    connection_cursor = connection.cursor()
    connection_cursor.execute("""
    SELECT files, station
    FROM captures
    """)

    all_watches_data = []

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

        all_watches_data.append({
            "station": station,
            "title": f"{station} - {day}/{month}/{year} - {base_name_without_ext}T.jpg",
            "date": f"{year}-{month}-{day} {hour}:{minute}:{second}",
            "permalink": f"/{year}/{month}/{day}/watch/{base_name_without_ext}",
            "capture": file.replace('P.jpg', 'T.jpg')
        })
    
    return all_watches_data


def generate_analyzers_data():
    connection = database.get_connection()
    connection_cursor = connection.cursor()
    connection_cursor.execute("""
    SELECT night_start, station
    FROM captures
    GROUP BY night_start, station
    """)
    
    all_analyzers_data = {}

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
            if base:
                all_analyzers_data[base[0]] = {
                    "station": station,
                    "class": classe,
                    "magnitude": magnitude,
                    "duration": duration,
                    "latitude_start": latitude_start,
                    "longitude_start": longitude_start,
                    "latitude_final": latitude_final,
                    "longitude_final": longitude_final,
                    "velocity": velocity,
                    "azimute_start": azimute_start,
                    "azimute_final": azimute_final,
                    "elevation_start": elevation_start,
                    "elevation_final": elevation_final,
                    "altitude_start": altitude_start,
                    "altitude_final": altitude_final
                }
    
    return all_analyzers_data


def generate_videos_data(output_dir: str = "./"):
    connection = database.get_connection()
    connection_cursor = connection.cursor()
    connection_cursor.execute("""
    SELECT files_full_path
    FROM captures
    """)

    all_videos_data = []

    for data in connection_cursor.fetchall():
        video_input = (data[0].replace('P.jpg', '.avi'))
        video_output = output_dir + "/" + os.path.basename(data[0].replace('P.jpg', '.mp4'))

        video.converter(video_input, video_output) # This still performs the conversion as a side effect
        
        all_videos_data.append({
            "input_path": video_input,
            "output_path": video_output,
            "converted": os.path.exists(video_output) # Indicate if conversion was successful
        })
    
    return all_videos_data


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

    all_output_data = {}

    print("- Generating captures data")
    all_output_data['captures'] = generate_captures_data()

    print("- Generating posts data")
    all_output_data['posts'] = generate_posts_data()

    print("- Generating watches data")
    all_output_data['watches'] = generate_watches_data()

    print("- Generating analyzers data")
    all_output_data['analyzers'] = generate_analyzers_data()

    print("- Generating videos data (and converting videos)")
    all_output_data['videos'] = generate_videos_data(configuration['storage']['videos'])

    print("- Uploading captures (Windows only)")
    captures.upload_captures(configuration['captures'], configuration['storage']['captures'])

    output_json_path = os.path.join(configuration['output']['base'], "output.json")
    print(f"- Writing all data to {output_json_path}")
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(all_output_data, f, ensure_ascii=False, indent=2)

    print("- Closing database connection")
    database.close_connection()

    print("- Done :)")