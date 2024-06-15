import asyncio
import logging
import time
from datetime import date

from aiogram import Bot
from aiogram import types

from aiogram.utils.exceptions import ChatNotFound, BotBlocked
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import ValidationError

from admin import Admin
from google_sheet import SheetGoogle
from user import User
from validators import TaskCreate
from storage import SQLiteStorage
from localized import Localized
from asyncio import sleep


class Form(StatesGroup):
    """
    State machine for data storage
    """
    number_tickets = State()
    comment = State()
    file = State()
    logins = State()
    fix_numer_tickets = State()


class BotTelegram:
    def __init__(self, config: dict, gs, db_admin, db_user, localized):
        """
        Bot initialization with the given configuration
        :param config: dictionary with bot configurations
        :param gs: SheetGoogle object
        :param db_admin: Admin object
        :param db_user: User object
        """
        self.storage = SQLiteStorage(config['db'])
        self.scheduler = AsyncIOScheduler()
        self.bot = Bot(token=config["token_bot"])
        self.superusers = config["superusers"].split(",")
        self.dp = Dispatcher(self.bot, storage=self.storage)
        self.gs: SheetGoogle = gs
        self.feedback_id_chat = config['feedback_id']
        self.additional_id = config['additional_id']
        self.db_admin: Admin = db_admin
        self.db_user: User = db_user
        self.localized: Localized = localized

        self.bot_commands = [
            BotCommand('start', "Запуск бота/Start bot"),
            BotCommand('switch_language', "Сменить язык/Switch language")

        ]

        self.button_lang_ru = InlineKeyboardButton(text='RU', callback_data='ru')
        self.button_lang_en = InlineKeyboardButton(text='EN', callback_data='en')
        self.inline_button = InlineKeyboardMarkup(row_width=4)
        self.inline_button.add(self.button_lang_ru).add(self.button_lang_en)

    async def start(self, message: types.Message):
        """
        Method of processing the start command
        """
        lang = await self.db_user.get_localized(message.from_user.id)
        logging.info(f'The /start command from  @{message.from_user.username} '
                     f'(full name: {message.from_user.full_name})')
        if str(message.from_user.id) in self.superusers or await self.db_admin.check_access(message.from_user.id):
            await message.reply(
                f"{self.localized.get_message('hello', lang)}, {message.from_user.first_name}",
                reply_markup=self.localized.get_keyboard('admin_button', lang))
        elif await self.db_user.get_name(message.from_user.id):
            await message.reply(
                f"{self.localized.get_message('hello', lang)}, {message.from_user.first_name}",
                reply_markup=self.localized.get_keyboard('get_task_butt', lang))

    async def send_commands(self, dp: Dispatcher):
        """
        Run when the bot starts, sends a set of commands
        """
        await dp.bot.set_my_commands(self.bot_commands)

    async def set_language(self, message: types.Message):
        await message.answer("Выберите язык / Choose your language:", reply_markup=self.inline_button)

    async def switch_language(self, callback: types.CallbackQuery):
        user_id = callback.from_user.id
        language = callback.data
        await self.db_admin.set_user_language(user_id, language)

        await callback.answer(f"Язык изменен на / Language changed to: {language}")

    async def get_job(self, message: types.Message, state: FSMContext):
        """
        Method for sending a message with information about the support
        """
        logging.info(f"Request for an assignment from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        lang = await self.db_user.get_localized(message.from_user.id)

        name = await self.db_user.get_name(message.from_user.id)
        if name:
            task = await self.db_user.get_support_line(message.from_user.id)
            if isinstance(task, tuple):
                time_now = date.today()
                finished_form = {"ru": f"Статус : {task[0]}\n"
                                       f"Дата начала оценки : {task[1]}\n"
                                       f"Логин : {task[2]}\n"
                                       f"Ссылка на оценку: <a href=\"{task[3]}\">{task[2]}</a>\n"
                                       f"Примечание : {task[4]}\n"
                                       f"Группа 2.0 : {task[5]}\n"
                                       f"Выработка : {task[7]}\n"
                                       f"Оценено : {task[8]}\n"
                                       f"Автопроверки : {task[9]}\n"
                                       f"Остаток : {task[10]}",
                                 "en": f"Status : {task[0]}\n"
                                       f"Date of assessment : {task[1]}\n"
                                       f"Login : {task[2]}\n"
                                       f"Evaluation link: <a href=\"{task[3]}\">{task[2]}</a>\n"
                                       f"Note : {task[4]}\n"
                                       f"Group 2.0 : {task[5]}\n"
                                       f"Productivity : {task[7]}\n"
                                       f"Assessed : {task[8]}\n"
                                       f"Autotests : {task[9]}\n"
                                       f"Remaining : {task[10]}"}

                data_dict = {
                    'login_support': task[2],
                    'date': time_now.strftime('%d.%m.%y'),
                    'login_kk': name,
                    'id_telegram': message.from_user.id,
                    'quantity_viewed_ticket': 0,
                    'timer': time.time(),
                    'comment': '',
                }
                await self.bot.send_message(message.from_user.id, text=finished_form[lang],
                                            parse_mode='HTML',
                                            reply_markup=self.localized.get_keyboard("button_change",
                                                                                     lang))
                logging.info(f"Task successfully completed {task[2]} for @{message.from_user.username} "
                             f"(full name: {message.from_user.full_name})")
                await Form.number_tickets.set()
                await self.bot.send_message(message.from_user.id,
                                            self.localized.get_message("count_tickets", lang),
                                            reply_markup=ReplyKeyboardRemove())
                async with state.proxy() as data:
                    data['data_dict'] = data_dict
            else:
                await self.bot.send_message(message.from_user.id, task)

    async def send_admin_message(self, message: types.Message):
        """
        Method for send message users
        """
        await sleep(10)
        if str(message.from_user.id) in self.superusers:
            notify = message.text.replace("/message", '')
            users = await self.db_admin.get_id_from_database()
            for i in users:
                try:
                    await self.bot.send_message(*i, notify)
                except (ChatNotFound, BotBlocked):
                    continue
                finally:
                    await sleep(1)

    async def number_of_tickets(self, message: types.Message, state: FSMContext):
        """
        Method of obtaining the number of evaluated tickets and then recording in google tables
        """
        lang = await self.db_user.get_localized(message.from_user.id)
        if message.text.isdigit():
            if int(message.text) == 0:
                await self.bot.send_message(message.from_user.id,
                                            self.localized.get_message('comment', lang),
                                            reply_markup=self.localized.get_keyboard('button_comment',
                                                                                     lang))
                await Form.comment.set()
            elif int(message.text) > 0:
                time_mess = await self.bot.send_message(message.from_user.id,
                                                        self.localized.get_message("waiting", lang))
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
                await self.bot.send_message(message.from_user.id, self.localized.get_message("count_rec", lang),
                                            reply_markup=self.localized.get_keyboard("get_task_butt", lang))
        else:
            await self.bot.send_message(message.from_user.id, self.localized.get_message("error_int", lang))

    async def comment(self, message: types.Message, state: FSMContext):
        """
         Method for recording a comment if no ticket has been checked
        """
        lang = await self.db_user.get_localized(message.from_user.id)
        time_mess = await self.bot.send_message(message.from_user.id, self.localized.get_message("waiting", lang))
        async with state.proxy() as data:
            data_dict: dict = data['data_dict']
        timer = time.time() - data_dict['timer']
        data_dict.update({'comment': message.text,
                          'timer': timer,
                          })
        await self.gs.spreadsheet_entry(**data_dict)
        await time_mess.delete()
        await state.finish()
        logging.info(f"Successful ticket skip, comment recorded for @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        await message.reply(self.localized.get_message("comment_rec", lang),
                            reply_markup=self.localized.get_keyboard("get_task_butt", lang))

    async def change_record_task(self, callback: types.CallbackQuery, state: FSMContext):
        """
        Corrects the number of tickets already recorded
        """
        logging.info(f"Request to change the number of tickets for correction from @{callback.from_user.username} "
                     f"(full name: {callback.from_user.full_name})")
        lang = await self.db_user.get_localized(callback.from_user.id)
        name = await self.db_user.get_name(callback.from_user.id)
        if name:
            data_message = callback.message.date
            if data_message.date() == date.today():
                message = callback.message.text
                list_task = message.split("\n")
                login = list_task[2].replace('Логин : ', '').replace("Login : ", '')
                await Form.fix_numer_tickets.set()
                async with state.proxy() as data:
                    data['login'] = login
                await self.bot.send_message(callback.from_user.id, self.localized.get_message("change_count", lang),
                                            reply_markup=self.localized.get_keyboard("button_cancel", lang))
                await callback.answer('🖊')
            else:
                await self.bot.send_message(callback.from_user.id,
                                            self.localized.get_message("info_old_task", lang),
                                            reply_markup=self.localized.get_keyboard("get_task_butt", lang))

    async def number_of_tickets_fixed(self, message: types.Message, state: FSMContext):
        """
        Requesting the number of tickets to be fixed
        """
        lang = await self.db_user.get_localized(message.from_user.id)
        value = message.text
        if value.isdigit():
            time_message = await self.bot.send_message(message.from_user.id,
                                                       self.localized.get_message("waiting_change", lang))
            async with state.proxy() as data:
                login: dict = data['login']
            result = await self.gs.change_number_tickets(login, str(message.from_user.id), value)
            await time_message.delete()
            match result:
                case 'Not found':
                    logging.info(f"Entry for login not found in table from @{message.from_user.username}"
                                 f" (full name: {message.from_user.full_name})")
                    await self.bot.send_message(message.from_user.id,
                                                self.localized.get_message("info_empty_entry", lang),
                                                reply_markup=self.localized.get_keyboard('get_task_butt', lang))
                case 'Error':
                    await self.bot.send_message(message.from_user.id,
                                                self.localized.get_message("info_error_entry", lang),
                                                reply_markup=self.localized.get_keyboard("get_task_butt", lang))
                case 'Successful':
                    logging.info(f"Changes to the task for {login} were successfully made "
                                 f"from @{message.from_user.username} (full name: {message.from_user.full_name})")
                    await self.bot.send_message(message.from_user.id,
                                                self.localized.get_message("success_change", lang),
                                                reply_markup=self.localized.get_keyboard("get_task_butt", lang))
            await state.finish()
        elif value in ('Отмена', 'Cancel'):
            logging.info(f"Cancellation for amendments from "
                         f"from @{message.from_user.username} (full name: {message.from_user.full_name})")
            await self.bot.send_message(message.from_user.id, self.localized.get_message("reset_change", lang),
                                        reply_markup=self.localized.get_keyboard("get_task_butt", lang))
            await state.finish()
        else:
            await message.reply(self.localized.get_message("wrong_count_ticket", lang))

    async def __update_support_rows_for_database(self):
        """
        Updating of the support lines
        :return:
        """
        try:
            rows = await self.gs.google_sheet_unloading_support_rows()
            await self.db_admin.unloading(rows)
        except Exception as e:
            logging.error('An error occurred during __update_support_rows_for_database method execution: %s', e)
            raise e

    async def unloading_from_tables(self, message: types.Message):
        """
        Method for updating the QC upload
        """
        logging.info(f"Table unload request from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        lang = await self.db_user.get_localized(message.from_user.id)
        if str(message.from_user.id) in self.superusers:
            time_mess = await self.bot.send_message(message.from_user.id,
                                                    self.localized.get_message("unloading_wait", lang))
            await self.__update_support_rows_for_database()
            logging.info(f"Successful upload for @{message.from_user.username} "
                         f"(full name: {message.from_user.full_name})")
            await time_mess.delete()
            await message.reply(self.localized.get_message("success_unloading", lang))

    async def priority_task(self, message: types.Message):
        """
        Method for updating the priority
        :param message:
        :return:
        """
        logging.info("Request to change priority from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        lang = await self.db_user.get_localized(message.from_user.id)
        if str(message.from_user.id) in self.superusers or await self.db_admin.check_access(message.from_user.id):
            await self.bot.send_message(message.from_user.id,
                                        self.localized.get_message("send_login", lang))
            await Form.logins.set()

    async def get_login_support(self, message: types.Message, state: FSMContext):
        """
        Method for obtaining logins
        :param message:
        :param state:
        :return:
        """
        lang = await self.db_user.get_localized(message.from_user.id)
        text = message.text
        list_login = text.split('\n')
        result = await self.db_admin.priority_setting(list_login)
        await state.finish()
        await message.reply(f'{self.localized.get_message("result_prior", lang)}\n{result}')
        logging.info("Successful priority change from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")

    async def user_update(self, message: types.Message):
        """
        Method for updating the User table
        """
        logging.info(f"Request to update the list of users from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        lang = await self.db_user.get_localized(message.from_user.id)
        if str(message.from_user.id) in self.superusers or await self.db_admin.check_access(message.from_user.id):
            user_list = await self.gs.employee_skills_update()
            await self.db_admin.user_update(user_list)
            logging.info(f"Successful update of the User base from @{message.from_user.username} "
                         f"(full name: {message.from_user.full_name})")
            await message.reply(self.localized.get_message("update_db", lang))

    async def user_skill_update(self, message: types.Message):
        """
        Method for updating skills
        """
        logging.info(f"Request to update the list skill of users from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        lang = await self.db_user.get_localized(message.from_user.id)
        if str(message.from_user.id) in self.superusers or await self.db_admin.check_access(message.from_user.id):
            user_list = await self.gs.employee_skills_update()
            await self.db_admin.skills_update(user_list)
            logging.info(f"Successful update of the User base from @{message.from_user.username} "
                         f"(full name: {message.from_user.full_name})")
            await message.reply(self.localized.get_message("update_db", lang))

    async def user_info(self, message: types.Message):
        """
        Method to get the list of users
        """
        logging.info(f"Request for a list of users from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        if str(message.from_user.id) in self.superusers or await self.db_admin.check_access(message.from_user.id):
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
        lang = await self.db_user.get_localized(message.from_user.id)
        if str(message.from_user.id) in self.superusers:
            list_admin = await self.gs.administrator_list_update()
            await self.db_admin.admin_update(list_admin)
            await message.reply(self.localized.get_message("update_db_root", lang))
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
        await self.send_commands(dp)
        self.scheduler.add_job(self.__update_support_rows_for_database, 'cron', hour=1, minute=0)
        self.scheduler.start()

    async def forward_feedback(self, message: types.Message):
        """
        Method for sending feedback
        """
        logging.info(f"The user @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name}) sent the file")
        lang = await self.db_user.get_localized(message.from_user.id)
        if await self.db_user.get_name(message.from_user.id):
            await self.bot.forward_message(self.feedback_id_chat, message.from_user.id, message.message_id)
            await message.reply(self.localized.get_message("get_oc", lang))

    async def additional_task(self, message: types.Message):
        """
        Method of receiving a message about additional tasks and recording them
        """
        lang = await self.db_user.get_localized(message.from_user.id)
        if str(message.chat.id) == self.additional_id:
            if await self.db_user.get_name(message.from_user.id):
                logging.info(f"A new task has been sent from @{message.from_user.username} "
                             f"(full name: {message.from_user.full_name})")
                text_chunks = message.text.split('\n')
                text_chunks = [i.strip() for i in text_chunks]
                try:
                    task = TaskCreate.from_list(text_chunks)
                    check_task = task.model_dump()
                    await self.gs.addition_task_entry(
                        check_task['login'],
                        check_task['task'],
                        check_task['date'],
                        check_task['quantity']
                    )
                    logging.info(f"The task is recorded in a google doc for @{message.from_user.username} "
                                 f"(full name: {message.from_user.full_name})")
                except (ValidationError, IndexError):
                    await message.reply(self.localized.get_message("wrong_add_task", lang))
                except ValueError:
                    await message.reply(self.localized.get_message("wrong_date_task", lang))

    async def error_handler(self, update: types.Update, exception):
        """
        Error handler in the aiogram library
        """
        logging.error(f'Caused by the update error: {exception}')
        return True

    def _reg_handlers(self, dp: Dispatcher):
        """
        registration of message handlers
        """
        dp.register_message_handler(self.start, commands="start")
        dp.register_message_handler(self.set_language, commands="switch_language")
        dp.register_message_handler(self.send_admin_message, commands='message')
        dp.register_message_handler(self.get_job, text=["Получить задание", "Get Task"], state=None)
        dp.register_message_handler(self.number_of_tickets, content_types='text', state=Form.number_tickets)
        dp.register_message_handler(self.comment, content_types='text', state=Form.comment)
        dp.register_callback_query_handler(self.change_record_task, text='change')
        dp.register_callback_query_handler(self.switch_language, text=['ru', 'en'])
        dp.register_message_handler(self.number_of_tickets_fixed, state=Form.fix_numer_tickets)
        dp.register_message_handler(self.unloading_from_tables, text=["Выгрузка", "Unload"])
        dp.register_message_handler(self.priority_task, text=["Приоритет", "Priority"], state=None)
        dp.register_message_handler(self.get_login_support, content_types='text', state=Form.logins)
        dp.register_message_handler(self.user_update, text=["Обновить аудиторов", "Update Auditors"])
        dp.register_message_handler(self.user_skill_update, text=["Обновить навыки", "Update Skills"])
        dp.register_message_handler(self.user_info, text=["Список аудиторов", "List of Auditors"])
        dp.register_message_handler(self.admin_update, text=["Обновить админов", "Update Admins"])
        dp.register_message_handler(self.get_log, text=["Логи", "Logs"])
        dp.register_message_handler(self.forward_feedback, content_types=('video', 'document', 'audio'))
        dp.register_message_handler(self.additional_task, regexp="#доп_задание")
        dp.register_errors_handler(self.error_handler)

    def run(self):
        """
        bot startup
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._reg_handlers(self.dp)
        executor.start_polling(self.dp, skip_updates=True, on_startup=self.on_startup, loop=loop)
