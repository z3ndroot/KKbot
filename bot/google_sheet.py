import logging

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
        self.addition_sheet_name = config['addition_sheet_name']
        self.addition_begin_column = config['addition_begin_column']
        self.head_task = config['head_task']

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
                                quantity_viewed_ticket: int, timer, comment=""):
        """
        Writing the result of the assessment in a google spreadsheet
        :param login_support: support login
        :param date: assessment date
        :param login_kk: quality control login
        :param id_telegram: user id
        :param quantity_viewed_ticket: number of tickets
        :param comment:
        :param timer:
        :return:
        """
        try:
            values = [login_support,
                      date,
                      login_kk,
                      id_telegram,
                      quantity_viewed_ticket,
                      timer,
                      comment]

            ss = await self.__authorize(self.table_id)

            selected_sheet = await ss.worksheet(self.task_sheet_name)
            await selected_sheet.append_row(values=values, table_range=self.task_begin_column)
        except Exception as e:
            logging.error('An error occurred during spreadsheet_entry method execution: %s', e)
            raise e

    async def addition_task_entry(self, login, task, date, quantity):
        """
        Method for recording additional jobs in google tables
        :param login: quality control login
        :param task: accomplished task
        :param date: task completion date
        :param quantity:
        :return:
        """
        try:
            ss = await self.__authorize(self.table_id)

            selected_sheet = await ss.worksheet(self.addition_sheet_name)
            await selected_sheet.append_row(values=[login, task, date, quantity],
                                            table_range=self.addition_begin_column)
        except Exception as e:
            logging.error('An error occurred during addition_task_entry method execution: %s', e)
            raise e

    async def google_sheet_unloading_support_rows(self):
        """
        Extracts all rows from Google table
        """
        try:
            ss = await self.__authorize(self.table_id)
            selected_sheet = await ss.worksheet(self.head_task)
            rows = await selected_sheet.get("A:K")
            return rows
        except Exception as e:
            logging.error('An error occurred during google_sheet_unloading_support_rows method execution: %s', e)
            raise e

    async def employee_skills_update(self):
        """
        Method for obtaining quality control staff and their skills
        :return: employee list
        """
        try:
            ss = await self.__authorize(self.table_id)
            selected_sheet = await ss.worksheet(self.user_sheet_name)
            result = await selected_sheet.get("A:C")

            return result
        except Exception as e:
            logging.error('An error occurred during employee_skills_update method execution: %s', e)
            raise e

    async def administrator_list_update(self):
        """
        Method offloads administrators
        :return: list of administrators
        """
        try:
            ss = await self.__authorize(self.table_id)
            selected_sheet = await ss.worksheet(self.admin_sheet_name)
            result = await selected_sheet.get("A:B")

            return result
        except Exception as e:
            logging.error('An error occurred during administrator_list_update method execution: %s', e)
            raise e

    async def change_number_tickets(self, support_login, telegram_id, value):
        """
        Makes changes to already recorded tasks
        :param support_login: support login from the message
        :param value: ticket quantity
        :param telegram_id: user id telegram
        :return:
        """
        try:
            ss = await self.__authorize(self.table_id)
            selected_sheet = await ss.worksheet(self.task_sheet_name)
            cell_list = await selected_sheet.findall(f'{support_login}')
            cell = cell_list[-1]
            get_user_id = await selected_sheet.cell(cell.row, cell.col + 3)
            if get_user_id.value != telegram_id:
                return 'Not found'
            await selected_sheet.update_cell(cell.row, cell.col + 4, value)
            return 'Successful'
        except Exception as e:
            logging.error('An error occurred during change_number_tickets method execution: %s', e)
            return 'Error'
