import asyncio
import logging
import os

from dotenv import load_dotenv

import google_sheet
import user


def main():
    load_dotenv()

    # Setup logging
    file_log = logging.FileHandler('chat.log')
    console_out = logging.StreamHandler()
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
                        handlers=(file_log, console_out))

    sheet_config = {'table_id': os.environ['SPREADSHEET_ID'],
                    'task_sheet_name': os.environ['TASK_SHEET_NAME'],
                    'task_begin_column': os.environ.get('TASK_BEGIN_COLUMN', 'A1'),
                    'user_sheet_name': os.environ['USER_SHEET_NAME'],
                    'admin_sheet_name': os.environ['ADMIN_SHEET_NAME']}

    db_config = {'db': os.environ['DB_PATH']}

    gs = google_sheet.SheetGoogle(sheet_config)
    user_db = user.User(db_config)


if __name__ == '__main__':
    main()
