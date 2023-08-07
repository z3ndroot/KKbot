from gspread_asyncio import AsyncioGspreadClientManager
from google.oauth2.service_account import Credentials


def get_creds():
    # To obtain a service account JSON file
    creds = Credentials.from_service_account_file("credentials.json")
    scoped = creds.with_scopes([
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ])
    return scoped


class SheetGoogle:
    def __init__(self, config: dict):
        """
        Initialization of spreadsheets with specified configuration
        :param config: dictionary with configurations for tables
        """
        self.agsm = AsyncioGspreadClientManager(get_creds)
        self.table_id = config["table_id"]
        self.task_sheet_name = config['task_sheet_name']
        self.task_begin_column = config['task_begin_column']

    async def spreadsheet_entry(self, login_support: str, date: str, login_kk: str, id_telegram: int,
                                quantity_viewed_ticket: int, comment=""):
        """
        Writing the result of the assessment in a google spreadsheet
        :param login_support: support login
        :param date: assessment date
        :param login_kk: quality control login
        :param id_telegram: user id
        :param quantity_viewed_ticket: number of tickets
        :param comment:
        :return:
        """
        values = [login_support,
                  date,
                  login_kk,
                  id_telegram,
                  quantity_viewed_ticket,
                  comment]

        agc = await self.agsm.authorize()
        ss = await agc.open_by_key(self.table_id)

        selected_sheet = await ss.worksheet(self.task_sheet_name)
        await selected_sheet.append_row(values=values, table_range=self.task_begin_column)
