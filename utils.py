import asyncio
import logging
import os
import re
import time
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import locale

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def fetch_roblox_id(username: str) -> int | None:
    res = requests.get(f"https://users.roblox.com/v1/users/search?keyword={username}")

    try:
        data = res.json()
        if "data" in data:
            return data["data"][0]["id"]
    except (KeyError, IndexError):
        return None
    
header_styles = {
    "backgroundColor": {
      "red": 0.92,
      "green": 0.82,
      "blue": 0.86
    },
    "horizontalAlignment": "CENTER",
    "textFormat": {
      "fontSize": 12,
      "bold": True
    }
}

row_styles = {
    "horizontalAlignment": "CENTER",
    "textFormat": {
      "fontSize": 10
    }
}

def write_to_ws(username: str, user_id: int, item: str, price: int) -> None:
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    gc = gspread.authorize(credentials)

    ss = gc.open_by_key(os.environ.get('SPREADSHEET_ID'))
    ws = ss.get_worksheet(0)

    current_time = datetime.now()
    date = current_time.strftime('%m/%d/%y')

    display_price = locale.currency(price, grouping=True)
    roblox_id = fetch_roblox_id(username) or ""

    data = [date, username, roblox_id, str(user_id), item, display_price]

    existing_data = ws.get_all_values()
    row = len(existing_data) + 1

    if len(existing_data) == 0 or data[0] != existing_data[-1][0]:
        header_row = ["Date", "User", "Customer (Roblox ID)", "Discord ID", "Item", "Amount", "Total Cost"]

        ws.append_row(header_row)
        ws.format(f"A{row}:G{row}", header_styles)
        row += 1

    ws.append_row(data)

    ws.format([f"A{row}", f"C{row}:D{row}"], {**row_styles, "textFormat": {"bold": False}})
    ws.format([f"B{row}", f"E{row}:G{row}"], {**row_styles, "textFormat": {"bold": True}})

    total_cost = price
    header_row = 0
    for i, row in enumerate(existing_data, start=2):
        if row[0] == date:
            total_cost += locale.atof(row[5].lstrip("$").replace(",", ""))
        if row[0] == "Date":
            header_row = i

    ws.update_cell(header_row, 7, locale.currency(total_cost, grouping=True))


class LogFormatter(logging.Formatter):
    LEVEL_COLOURS = [
        (logging.DEBUG, "\x1b[40;1m"),
        (logging.INFO, "\x1b[34;1m"),
        (logging.WARNING, "\x1b[33;1m"),
        (logging.ERROR, "\x1b[31m"),
        (logging.CRITICAL, "\x1b[41m"),
    ]

    FORMATS = {
        level: logging.Formatter(
            f"\x1b[30;1m%(asctime)s\x1b[0m {colour}%(levelname)-8s\x1b[0m \x1b[35m%(name)s\x1b[0m %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
        for level, colour in LEVEL_COLOURS
    }

    def colorize_args(self, record: logging.LogRecord) -> str:
        msg = str(record.msg)
        for arg in record.args:
            placeholder = re.search(r"%\w+", msg)

            if placeholder:
                msg = msg.replace(placeholder.group(), f"\x1b[34m{arg}\x1b[0m", 1)

        return msg

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        # Override the args to print in blue
        if record.args:
            record.msg = self.colorize_args(record)
            # Remove the args so the default formatter doesn't print them
            record.args = ()

        # Override the traceback to always print in red
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f"\x1b[31m{text}\x1b[0m"

        output = formatter.format(record)

        # Remove the cache layer
        record.exc_text = None
        return output


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(LogFormatter())

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
