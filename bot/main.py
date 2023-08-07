from dotenv import load_dotenv
import logging
import google_sheet
import asyncio
import os


def main():
    load_dotenv()

    # Setup logging
    file_log = logging.FileHandler('chat.log')
    console_out = logging.StreamHandler()
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
                        handlers=(file_log, console_out))

    sheet_config = {'table_id': os.environ['SPREADSHEET_ID'],
                    'task_sheet_name': os.environ['TASK_SHEET_NAME'],
                    'task_begin_column': os.environ.get('TASK_BEGIN_COLUMN', 'A1')}

    gs = google_sheet.SheetGoogle(sheet_config)


if __name__ == '__main__':
    main()
