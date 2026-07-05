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

            # normalizar barras e tentar extrair o caminho relativo a partir do nome da estação
            norm_path = stack_image_path.replace("\\", "/")
            token = f"{station}/"
            if token in norm_path:
                preview = station + "/" + norm_path.split(token, 1)[1]
            else:
                idx = norm_path.find(station)
                if idx != -1:
                    preview = norm_path[idx:].lstrip("/\\")
                else:
                    preview = f"{station}/{os.path.basename(norm_path)}"

            all_captures_data.append({
                "night_start": night_start,
                "station": station,
                "title": f"Capturas da estação {station}",
                "preview": preview,
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
        analyze =  file.replace('P.jpg', 'A.XML')

        if not os.path.exists(analyze):
            continue

        try:
            xmldoc = minidom.parse(analyze)
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

        all_analyzer_data = {
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

        all_watches_data.append({
            "station": station,
            "title": f"{station} - {day}/{month}/{year} - {base_name_without_ext}T.jpg",
            "date": f"{year}-{month}-{day} {hour}:{minute}:{second}",
            "permalink": f"/{year}/{month}/{day}/watch/{base_name_without_ext}",
            "capture": file.replace('P.jpg', 'T.jpg'),
            "video": file.replace('P.jpg', 'T.mp4'),
            "analyzer": all_analyzer_data
        })
    
    return all_watches_data


if __name__ == '__main__':
    print("- Loading site configuration")
    configuration = config.load_config()

    print("- Reading captures")
    days_limit = configuration.get('days')
    if days_limit is not None and isinstance(days_limit, int) and days_limit > 0:
        files_captures = captures.get_captures([configuration['storage']['captures']], days_limit)
    else:
        # If 'days' is not specified, empty, or not a positive integer, read all
        files_captures = captures.get_captures([configuration['storage']['captures']], None)

    if len(files_captures) == 0:
        print("- Nothing to do")
        print("- Closing database connection")

        exit(0)

    all_output_data = {}

    print("- Generating captures data")
    all_output_data['captures'] = generate_captures_data()

    print("- Generating posts data")
    all_output_data['posts'] = generate_posts_data()

    print("- Generating watches data")
    all_output_data['watches'] = generate_watches_data()

    output_json_path = os.path.join(configuration['output']['base'], "capturas.json")
    print(f"- Writing all data to {output_json_path}")
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(all_output_data, f, ensure_ascii=False, indent=2)

    print("- Done :)")
    