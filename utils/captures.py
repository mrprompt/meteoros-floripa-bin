import glob
import re
from . import utils


def get_matching_captures(captures_dir: list, days: int) -> list[str]:
    result = []
    date_list = utils.get_date_list(days)

    for directory in captures_dir:
        for date in date_list:
            files = glob.glob("{}/**/{}/*P.jpg".format(directory, date), recursive=True)

            result.extend(files)

    return utils.fix_path_delimiter(result)


def organize_captures(stations_captures):
    def populate_tables(captures_list: list):
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


def get_captures(captures_dir: list, days: int) -> list[str]:
    files_captures = get_matching_captures(captures_dir, days)

    organize_captures(files_captures)

    return files_captures
