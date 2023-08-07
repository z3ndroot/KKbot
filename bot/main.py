from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import logging

def get_creds():
    # To obtain a service account JSON file
    creds = Credentials.from_service_account_file("credentials.json")
    scoped = creds.with_scopes([
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ])
    return scoped


def main():
    load_dotenv()

    # Setup logging
    file_log = logging.FileHandler('log/chat.log')
    console_out = logging.StreamHandler()
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
                        handlers=(file_log, console_out))
