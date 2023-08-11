import json
import re
from datetime import datetime

from google.oauth2.service_account import Credentials
from gspread_asyncio import AsyncioGspreadClientManager


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
        self.__agsm = AsyncioGspreadClientManager(get_creds)
        self.table_id = config["table_id"]
        self.task_sheet_name = config['task_sheet_name']
        self.task_begin_column = config['task_begin_column']
        self.user_sheet_name = config['user_sheet_name']
        self.admin_sheet_name = config['admin_sheet_name']
        self.__today_date = datetime.now()

    async def __authorize(self, table_id):
        """
        Authorization method in google spreadsheets
        :param table_id: google table id
        :return:
        """
        agc = await self.__agsm.authorize()
        ss = await agc.open_by_key(table_id)
        return ss

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

        ss = await self.__authorize(self.table_id)

        selected_sheet = await ss.worksheet(self.task_sheet_name)
        await selected_sheet.append_row(values=values, table_range=self.task_begin_column)

    async def google_sheet_unloading_support_rows(self):
        """
        Extracts all rows from Google table with support staff by skill and converts to a json file
        """
        ss = await self.__authorize(self.table_id)

        selected_sheet = await ss.get_worksheet(0)
        s = await selected_sheet.get_all_values()

        with open('google_table/work.json', "r", encoding="UTF8") as file:  # открываем json файл с навыками всех КК
            json_dump = file.read()
            json_read = json.loads(json_dump)

        for value in s:
            if value[6] in json_read and (value[0] == "" or value[0] == "НЕ ДЕКРЕТ") and value[10] != "0":
                if value[1] == "-" or value[1] == "" or (re.match('\d{2}\.\d{2}\.\d{4}', value[1])
                                                         and self.__today_date > datetime.strptime(value[1],
                                                                                                   "%d.%m.%Y")):
                    json_read[value[6]].append(value[0:10])
        with open('google_table/unloading.json', "w", encoding="UTF8") as file:
            file.write(json.dumps(json_read, indent=4, ensure_ascii=False))

    async def employee_skills_update(self):
        """
        Method for obtaining quality control staff and their skills
        :return: employee list
        """
        ss = await self.__authorize(self.table_id)

        selected_sheet = await ss.worksheet(self.user_sheet_name)
        result = await selected_sheet.get_all_values()
        result = [i[0:3] for i in result]
        return result
