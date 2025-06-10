import glob
import re
import sys
from . import utils, database
from robocopy import robocopy
from PIL import ImageChops, Image
from typing import List, Tuple

CaptureRecord = Tuple[str, str, str, str]


def get_matching_captures(captures_dir: List[str], days: int) -> List[str]:
    result: list[str] = []
    date_list = utils.get_date_list(days)

    for directory in captures_dir:
        for date in date_list:
            files = glob.glob("{}/**/{}/*P.jpg".format(directory, date), recursive=True)

            result.extend(files)

    return utils.fix_path_delimiter(result)


def organize_captures(stations_captures: list[str]):
    captures_organized: list[CaptureRecord] = []

    for capture in stations_captures:
        base = re.findall(r"\w{3,5}\d{1,2}.+P\.jpg$", capture)
        capture_spliced = base[0].split('/')
        station = capture_spliced[0]
        capture_date = capture_spliced[3]
        post: CaptureRecord = (capture_date, station, base[0], capture)

        captures_organized.append(post)

    database.populate_tables(captures_organized)


def get_captures(captures_dir: List[str], days: int) -> list[str]:
    files_captures = get_matching_captures(captures_dir, days)

    organize_captures(files_captures)

    return files_captures


def stack(data: list[str], output_file: str):
    try:
        stack = Image.open(data[0])

        for i in range(1, len(data)):
            current_image = Image.open(data[i])
            stack = ImageChops.lighter(stack, current_image)

        stack.save(output_file, "JPEG")
    except:
        pass


def upload_captures(sources: List[str], captures_dest: str) -> None:
    is_windows = hasattr(sys, 'getwindowsversion')

    if not is_windows:
        return

    for source in sources:
        try:
            robocopy.copy(source, captures_dest, "/xf *.mp4 /xf *.avi /xo") # type: ignore
        except Exception as e:
            print('Some error occurred uploading capture: ' + str(e))


def populate_tables(captures_list: List[CaptureRecord]) -> None:
    connection = database.get_connection()
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
