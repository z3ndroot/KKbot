import asyncio
import json
import logging
import time
from datetime import date

import aiofiles
from aiogram import Bot
from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from admin import Admin
from google_sheet import SheetGoogle
from user import User


class Form(StatesGroup):
    """
    State machine for data storage
    """
    number_tickets = State()
    comment = State()
    file = State()


class BotTelegram:
    def __init__(self, config: dict, gs, db_admin, db_user):
        """
        Bot initialization with the given configuration
        :param config: dictionary with bot configurations
        :param gs: SheetGoogle object
        :param db_admin: Admin object
        :param db_user: User object
        """
        self.storage = MemoryStorage()
        self.scheduler = AsyncIOScheduler()
        self.bot = Bot(token=config["token_bot"])
        self.superusers = config["superusers"].split(",")
        self.dp = Dispatcher(self.bot, storage=self.storage)
        self.gs: SheetGoogle = gs
        self.db_admin: Admin = db_admin
        self.db_user: User = db_user
        self.button_comment = [
            KeyboardButton('нет тикетов'),
            KeyboardButton('нет смен'),
            KeyboardButton('уволен'),
            KeyboardButton('больничный'),
            KeyboardButton('отпуск/обс'),
        ]
        self.get_task_butt = KeyboardButton('Получить задание')
        self.admin_button = [
            KeyboardButton('Обновить навыки'),
            KeyboardButton('Обновить админов'),
            KeyboardButton('Обновить аудиторов'),
            KeyboardButton('Обновить группы'),
            KeyboardButton('Список аудиторов'),
            KeyboardButton('Список групп'),
            KeyboardButton('Выгрузка'),
            KeyboardButton('Логи'),
        ]
        self.buttons_comment = ReplyKeyboardMarkup(resize_keyboard=True)
        self.buttons_comment.add(*self.button_comment)
        self.get_task = ReplyKeyboardMarkup(resize_keyboard=True)
        self.get_task.add(self.get_task_butt)
        self.admin_buttons = ReplyKeyboardMarkup(resize_keyboard=True)
        self.admin_buttons.add(self.admin_button[0]).insert(self.admin_button[1])
        self.admin_buttons.add(self.admin_button[2]).insert(self.admin_button[3])
        self.admin_buttons.add(self.admin_button[4]).insert(self.admin_button[5])
        self.admin_buttons.add(self.admin_button[6]).add(self.admin_button[7])

    async def start(self, message: types.Message):
        """
        Method of processing the start command
        """
        logging.info(f'The /start command from  @{message.from_user.username} '
                     f'(full name: {message.from_user.full_name})')
        if str(message.from_user.id) in self.superusers or await self.db_admin.check_access(str(message.from_user.id)):
            await message.reply(f"Привет, {message.from_user.first_name}", reply_markup=self.admin_buttons)
        elif await self.db_user.get_name(str(message.from_user.id)):
            await message.reply(f"Привет, {message.from_user.first_name}", reply_markup=self.get_task)

    async def get_job(self, message: types.Message, state: FSMContext):
        """
        Method for sending a message with information about the support
        """
        logging.info(f"Request for an assignment from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")

        name = await self.db_user.get_name(str(message.from_user.id))
        if name:
            skill = await self.db_user.output_skill_counter(str(message.from_user.id))
            task = await self.distributor(skill)
            if isinstance(task, list):
                time_now = date.today()
                finished_form = (f"Статус : {task[0]}\n"
                                 f"Логин : {task[2]}\n"
                                 f"Ссылка на оценку: <a href=\"{task[3]}\">{task[2]}</a>\n"
                                 f"Примечание : {task[4]}\n"
                                 f"Группа 2.0 : {task[5]}\n"
                                 f"Выработка : {task[7]}\n"
                                 f"Оценено : {task[8]}\n"
                                 f"Автопроверки : {task[9]}\n"
                                 f"Остаток : {task[10]}")

                data_dict = {
                    'login_support': task[2],
                    'date': time_now.strftime('%d.%m.%y'),
                    'login_kk': name,
                    'id_telegram': message.from_user.id,
                    'quantity_viewed_ticket': 0,
                    'timer': time.time(),
                    'comment': '',
                }
                await self.bot.send_message(message.from_user.id, text=finished_form, parse_mode='HTML')
                logging.info(f"Task successfully completed {task[2]} for @{message.from_user.username} "
                             f"(full name: {message.from_user.full_name})")
                await Form.number_tickets.set()
                await self.bot.send_message(message.from_user.id, "Введи кол-во оценённых тикетов:",
                                            reply_markup=ReplyKeyboardRemove())
                async with state.proxy() as data:
                    data['data_dict'] = data_dict
            else:
                await self.bot.send_message(message.from_user.id, task)

    async def number_of_tickets(self, message: types.Message, state: FSMContext):
        """
        Method of obtaining the number of evaluated tickets and then recording in google tables
        """
        if message.text.isdigit():
            if int(message.text) == 0:
                await self.bot.send_message(message.from_user.id,
                                            "⚠Напишите комментарий к агенту⚠:",
                                            reply_markup=self.buttons_comment)
                await Form.comment.set()
            elif int(message.text) > 0:
                time_mess = await self.bot.send_message(message.from_user.id, '⏱Пожалуйста подождите.....')
                async with state.proxy() as data:
                    data_dict: dict = data['data_dict']
                timer = time.time() - data_dict['timer']
                data_dict.update({'quantity_viewed_ticket': int(message.text),
                                  'timer': timer
                                  })
                await self.gs.spreadsheet_entry(**data_dict)
                logging.info(f"Successful google table entry for a user @{message.from_user.username} "
                             f"(full name: {message.from_user.full_name})")
                await time_mess.delete()
                await state.finish()
                await self.bot.send_message(message.from_user.id, "Количество записано✅", reply_markup=self.get_task)
        else:
            await self.bot.send_message(message.from_user.id, "Ответ должно содержать целое число!!!")

    async def comment(self, message: types.Message, state: FSMContext):
        """
         Method for recording a comment if no ticket has been checked
        """
        time_mess = await self.bot.send_message(message.from_user.id, "⏱Пожалуйста подождите.....")
        async with state.proxy() as data:
            data_dict: dict = data['data_dict']
        timer = time.time() - data_dict['timer']
        data_dict.update({'comment': message.text,
                          'timer': timer,
                          })
        await self.gs.spreadsheet_entry(**data_dict)
        logging.info(f"Successful ticket skip, comment recorded for @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        await time_mess.delete()
        await state.finish()
        await message.reply("Комментарий записан✅", reply_markup=self.get_task)

    @staticmethod
    async def distributor(skill):
        """
        Static method for skill allocation
        :param skill: User skill
        """
        async with aiofiles.open("google_table/unloading.json", 'r', encoding="UTF8") as file:
            file_content = await file.read()
            templates = json.loads(file_content)
        task_support = templates.get(skill, "Нет навыка")
        if not task_support:
            return f"Нет активных задач по навыку {skill}("
        if task_support != 'Нет навыка':
            support_kk = max(task_support, key=lambda sort_sup: int(sort_sup[10]))
            task_support.remove(support_kk)
            templates[skill] = task_support
            async with aiofiles.open("google_table/unloading.json", "w", encoding="UTF8") as file:
                await file.write(json.dumps(templates, indent=4, ensure_ascii=False))
            return support_kk
        else:
            return f"Проблемы с навыком {skill}, обратись к рг("

    async def unloading_from_tables(self, message: types.Message):
        """
        Method for updating the QC upload
        """
        logging.info(f"Table unload request from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        if str(message.from_user.id) in self.superusers:
            time_mess = await self.bot.send_message(message.from_user.id, "⏱Выгрузка. Пожалуйста подождите.....")
            await self.gs.google_sheet_unloading_support_rows()
            logging.info(f"Successful upload for @{message.from_user.username} "
                         f"(full name: {message.from_user.full_name})")
            await time_mess.delete()
            await message.reply("Выгрузка обновлена✅")

    async def filter_update(self, message: types.Message):
        """
        Method for requesting a filter update
        """
        logging.info(f"Filter update request from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        if str(message.from_user.id) in self.superusers or self.db_admin.check_access(str(message.from_user.id)):
            await self.bot.send_message(message.from_user.id, 'Отправь мне файл work.json')
            await Form.file.set()

    async def filter_download(self, message: types.Message, state: FSMContext):
        """
        Method for loading the filter
        """
        file_id = message.document.file_id
        file = await self.bot.get_file(file_id)
        file_path = file.file_path
        await self.bot.download_file(file_path, 'google_table/work.json')
        try:
            async with aiofiles.open('google_table/work.json', 'r', encoding="UTF8") as file:
                file_content = await file.read()
                json.loads(file_content)
            logging.info(f"Filter has been successfully loaded for @{message.from_user.username} "
                         f"(full name: {message.from_user.full_name})")
            await message.reply("Файл загружен✅")
            await state.finish()
        except ValueError as e:
            logging.warning('The filter is not correct %s', e)
            await message.reply(f"Файл некорректный❌({e})")

    async def filter_info(self, message: types.Message):
        """
        Method for sending a filter file
        """
        logging.info(f"Filter unloading request from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        if str(message.from_user.id) in self.superusers or self.db_admin.check_access(str(message.from_user.id)):
            await self.bot.send_document(message.from_user.id, open("google_table/work.json", 'rb'))
            logging.info(f"The file work.json has been sent @{message.from_user.username} "
                         f"(full name: {message.from_user.full_name})")

    async def user_update(self, message: types.Message):
        """
        Method for updating the User table
        """
        logging.info(f"Request to update the list of users from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        if str(message.from_user.id) in self.superusers or self.db_admin.check_access(str(message.from_user.id)):
            user_list = await self.gs.employee_skills_update()
            await self.db_admin.user_update(user_list)
            logging.info(f"Successful update of the User base from @{message.from_user.username} "
                         f"(full name: {message.from_user.full_name})")
            await message.reply("База данных обновлена✅")

    async def user_skill_update(self, message: types.Message):
        """
        Method for updating skills
        """
        logging.info(f"Request to update the list skill of users from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        if str(message.from_user.id) in self.superusers or self.db_admin.check_access(str(message.from_user.id)):
            user_list = await self.gs.employee_skills_update()
            await self.db_admin.skills_update(user_list)
            logging.info(f"Successful update of the User base from @{message.from_user.username} "
                         f"(full name: {message.from_user.full_name})")
            await message.reply("База данных обновлена✅")

    async def user_info(self, message: types.Message):
        """
        Method to get the list of users
        """
        logging.info(f"Request for a list of users from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        if str(message.from_user.id) in self.superusers or self.db_admin.check_access(str(message.from_user.id)):
            await self.db_admin.get_user_from_database()
            await self.bot.send_document(message.from_user.id, open('db/user.json', 'rb'))
            logging.info(f"The file user.json has been sent @{message.from_user.username} "
                         f"(full name: {message.from_user.full_name})")

    async def admin_update(self, message: types.Message):
        """
        A method for renewing admins
        """
        logging.info(f"Request to update the list of admins from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        if str(message.from_user.id) in self.superusers:
            list_admin = await self.gs.administrator_list_update()
            await self.db_admin.admin_update(list_admin)
            await message.reply("База данных Администраторов обновлена✅")
            logging.info(f"Successful update of the Admin base from @{message.from_user.username} "
                         f"(full name: {message.from_user.full_name})")

    async def get_log(self, message: types.Message):
        """
        Method for unloading the log
        """
        logging.info(f"Request to unload logs from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        if str(message.from_user.id) in self.superusers:
            await self.bot.send_document(message.from_user.id, open('log/chat.log', 'rb'))

    async def on_startup(self, dp: Dispatcher):
        """
        Automatic unloading
        """
        self.scheduler.add_job(self.gs.google_sheet_unloading_support_rows, 'cron', hour=1, minute=0)
        self.scheduler.start()

    def _reg_handlers(self, dp: Dispatcher):
        """
        registration of message handlers
        """
        dp.register_message_handler(self.start, commands="start")
        dp.register_message_handler(self.get_job, text="Получить задание", state=None)
        dp.register_message_handler(self.number_of_tickets, content_types='text', state=Form.number_tickets)
        dp.register_message_handler(self.comment, content_types='text', state=Form.comment)
        dp.register_message_handler(self.unloading_from_tables, text='Выгрузка')
        dp.register_message_handler(self.filter_update, text="Обновить группы")
        dp.register_message_handler(self.filter_download, content_types=types.ContentType.DOCUMENT, state=Form.file)
        dp.register_message_handler(self.filter_info, text="Список групп")
        dp.register_message_handler(self.user_update, text="Обновить аудиторов")
        dp.register_message_handler(self.user_skill_update, text='Обновить навыки')
        dp.register_message_handler(self.user_info, text='Список аудиторов')
        dp.register_message_handler(self.admin_update, text='Обновить админов')
        dp.register_message_handler(self.get_log, text='Логи')

    def run(self):
        """
        bot startup
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._reg_handlers(self.dp)
        executor.start_polling(self.dp, skip_updates=True, on_startup=self.on_startup, loop=loop)
