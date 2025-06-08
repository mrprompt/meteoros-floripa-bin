import datetime


def get_date_list(days: int, date_format: str = '%Y%m%d'):
    return [(datetime.date.today() - datetime.timedelta(days=x)).strftime(date_format) for x in range(0, days)]


def fix_path_delimiter(captures_list: list[str]) -> list[str]:
    result = []

    for path in captures_list:
        path_fixed = path.replace("\\", "/")

        result.append(path_fixed)

    return result
