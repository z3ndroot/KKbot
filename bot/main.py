import logging
import os

from dotenv import load_dotenv

import google_sheet
from user import User
from admin import Admin
from bot_tg import BotTelegram


def main():
    load_dotenv()

    # Setup logging
    file_log = logging.FileHandler('log/chat.log')
    console_out = logging.StreamHandler()
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
                        handlers=(file_log, console_out))

    sheet_config = {'table_id': os.environ['SPREADSHEET_ID'],
                    'task_sheet_name': os.environ['TASK_SHEET_NAME'],
                    'task_begin_column': os.environ.get('TASK_BEGIN_COLUMN', 'A1'),
                    'user_sheet_name': os.environ['USER_SHEET_NAME'],
                    'admin_sheet_name': os.environ['ADMIN_SHEET_NAME']}

    db_config = {'db': os.environ['DB_PATH']}

    bot_config = {'token_bot': os.environ['TOKEN_TELEGRAM'],
                  'superusers': os.environ['SUPERUSER']}

    gs = google_sheet.SheetGoogle(sheet_config)
    db_admin = Admin(db_config)
    db_user = User(db_config)
    bot_tg = BotTelegram(bot_config, gs, db_admin, db_user)
    bot_tg.run()


if __name__ == '__main__':
    main()
