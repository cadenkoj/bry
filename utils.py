import json
import locale
import logging
import os
import re
from datetime import datetime, timedelta

import discord
import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials

from constants import *

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def calc_discount(total, item_count):
 if item_count >= 2 and total >= 50:
     discount = (total // 50) * 5
     return min(discount, 50)
 else:
     return 0
 
def split_list(lst, chunk_size):
    return [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size)]

def fetch_roblox_id(username: str) -> int | None:
    try:
        payload = json.dumps({
          "usernames": [username],
          "excludeBannedUsers": True
        })

        headers = {
          'Content-Type': 'application/json'
        }

        res = requests.post(f"https://users.roblox.com/v1/usernames/users", data=payload, headers=headers)
        res.raise_for_status()

        data = res.json()

        if "data" in data:
            return data["data"][0]["id"]
    except:
        return None
    
header_styles = {
    "backgroundColor": {
      "red": 0.92,
      "green": 0.82,
      "blue": 0.86,
    },
    "horizontalAlignment": "CENTER",
    "textFormat": {
      "fontSize": 12,
      "bold": True,
    }
}

row_styles = {
    "backgroundColor": {
      "red": 1,
      "green": 1,
      "blue": 1,
    },
    "horizontalAlignment": "CENTER",
    "textFormat": {
      "fontSize": 10,
    }
}

def write_to_ws(new_total: int, username: str, user_id: int, item: str, price: int) -> None:
    if not IS_PROD:
        return

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

    header_row = 0
    for i, row in enumerate(existing_data, start=2):
        if row[0] == "Date":
            header_row = i

    ws.update_cell(header_row, 7, locale.currency(new_total, grouping=True))

def parse_human_duration(duration: str) -> timedelta:
    components = {
        "weeks": 0,
        "days": 0,
        "hours": 0,
        "minutes": 0,
        "seconds": 0,
    }

    for key in components:
        match = re.search(rf"(\d+){key[0]}", duration)
        if match:
            components[key] = int(match.group(1))

    current_time = datetime.now()
    delta_time = timedelta(**components)

    if current_time == current_time + delta_time:
        raise ValueError("Invalid input format. Use the 'XhYm' format. e.g. '1h30m'")

    return delta_time

@dataclass
class UserLog:
    user: discord.User
    moderator: discord.Member
    reason: str

@dataclass
class MemberLog:
    user: discord.Member
    moderator: discord.Member
    reason: str

@dataclass
class ActionCache:
    kick: UserLog
    unban: UserLog
    ban: MemberLog
    unmute: MemberLog
    mute: MemberLog
    
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

# chrome_service = webdriver.ChromeService()
# chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--headless')
# chrome_options.add_argument('--no-sandbox')
# chrome_options.add_argument('--disable-dev-shm-usage')

# driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

# async def parse_cash_app_receipt(url: str) -> tuple[str, bool]:
#     parsed_url = urlparse(url)

#     if parsed_url.netloc != "cash.app":
#         return "Invalid URL. Please provide a valid Cash App web receipt.", False
    
#     try:
#         driver.get(url)

#         header_info = EC.presence_of_element_located((By.XPATH, "//h4[contains(text(),'Payment to $ehxpulse')]"))
#         WebDriverWait(driver, 5).until(header_info)

#         note = driver.find_element(By.XPATH, "//p[contains(text(),'For')]").text
#         info = driver.find_elements(By.TAG_NAME, "dd")

#         amount = info[0].text
#         source = info[1].text

#         if note != "For gift":
#             return "Invalid note. Please wait for refund and send with the note \"gift\".", False
        
#         if source != "Cash":
#             return "Invalid source. Please wait for refund and send with Cash Balance.", False

#         return amount, True
    
#     except NoSuchElementException:
#         return "Invalid Cash App transaction.", False

#     except TimeoutException:
#         return "Timed out reading Cash App web receipt.", False