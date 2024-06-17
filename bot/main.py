import logging
import os

from dotenv import load_dotenv

import google_sheet
from user import User
from admin import Admin
from bot_tg import BotTelegram
from localized import Localized


def check_folders(folders: list):
    """
    Creating folders if they are missing
    :param folders:
    :return: list missing folders
    """
    missing_folder = []
    for folder in folders:
        if not os.path.isdir(folder):
            os.mkdir(folder)
            missing_folder.append(folder)
    return missing_folder


def main():
    load_dotenv()

    # Check missing folders
    folders = ['db', 'log']
    missing_folder = check_folders(folders)

    # Setup logging
    file_log = logging.FileHandler('log/chat.log')
    console_out = logging.StreamHandler()
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
                        handlers=(file_log, console_out))

    if len(missing_folder) > 0:
        logging.info(f'These folders {", ".join(missing_folder)} were missing and were successfully created')

    sheet_config = {'table_id': os.environ['SPREADSHEET_ID'],
                    'task_sheet_name': os.environ['TASK_SHEET_NAME'],
                    'task_begin_column': os.environ.get('TASK_BEGIN_COLUMN', 'A1'),
                    'user_sheet_name': os.environ['USER_SHEET_NAME'],
                    'admin_sheet_name': os.environ['ADMIN_SHEET_NAME'],
                    'addition_sheet_name': os.environ['ADDITION_SHEET_NAME'],
                    'addition_begin_column': os.environ['ADDITION_BEGIN_COLUMN'],
                    'head_task': os.environ['HEAD_TASK']}

    db_config = {'db': os.environ['DB_PATH']}

    bot_config = {'token_bot': os.environ['TOKEN_TELEGRAM'],
                  'superusers': os.environ['SUPERUSER'],
                  'feedback_id': os.environ['FEEDBACK_ID'],
                  'additional_id': os.environ['ADDITIONAL_ID'],
                  'db': os.environ['DB_PATH']}

    gs = google_sheet.SheetGoogle(sheet_config)
    db_admin = Admin(db_config)
    db_user = User(db_config)
    localized = Localized()
    bot_tg = BotTelegram(bot_config, gs, db_admin, db_user, localized)
    bot_tg.run()


if __name__ == '__main__':
    main()
