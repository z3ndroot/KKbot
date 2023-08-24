import asyncio
import logging
import time
from datetime import date

from aiogram import Bot
from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import ValidationError

from admin import Admin
from google_sheet import SheetGoogle
from user import User
from validators import TaskCreate


class Form(StatesGroup):
    """
    State machine for data storage
    """
    number_tickets = State()
    comment = State()
    file = State()
    logins = State()


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
        self.feedback_id_chat = config['feedback_id']
        self.additional_id = config['additional_id']
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
            KeyboardButton('Список аудиторов'),
            KeyboardButton('Приоритет'),
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
        self.admin_buttons.add(self.admin_button[4]).add(self.admin_button[5]).add(self.admin_button[6])

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
            task = await self.db_user.get_support_line(message.from_user.id)
            if isinstance(task, tuple):
                time_now = date.today()
                finished_form = (f"Статус : {task[0]}\n"
                                 f"Дата начала оценки : {task[1]}\n"
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
        if str(message.from_user.id) in self.superusers:
            time_mess = await self.bot.send_message(message.from_user.id, "⏱Выгрузка. Пожалуйста подождите.....")
            await self.__update_support_rows_for_database()
            logging.info(f"Successful upload for @{message.from_user.username} "
                         f"(full name: {message.from_user.full_name})")
            await time_mess.delete()
            await message.reply("Выгрузка обновлена✅")

    async def priority_task(self, message: types.Message):
        """
        Method for updating the priority
        :param message:
        :return:
        """
        logging.info("Request to change priority from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        if str(message.from_user.id) in self.superusers or await self.db_admin.check_access(str(message.from_user.id)):
            await self.bot.send_message(message.from_user.id,
                                        "Отправь мне список логинов в формате:\ntest\ntest2\ntest3")
            await Form.logins.set()

    async def get_login_support(self, message: types.Message, state: FSMContext):
        """
        Method for obtaining logins
        :param message:
        :param state:
        :return:
        """
        text = message.text
        list_login = text.split('\n')
        result = await self.db_admin.priority_setting(list_login)
        await state.finish()
        await message.reply(f'Результаты обновления приоритета:\n{result}')
        logging.info("Successful priority change from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")

    async def user_update(self, message: types.Message):
        """
        Method for updating the User table
        """
        logging.info(f"Request to update the list of users from @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name})")
        if str(message.from_user.id) in self.superusers or await self.db_admin.check_access(str(message.from_user.id)):
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
        if str(message.from_user.id) in self.superusers or await self.db_admin.check_access(str(message.from_user.id)):
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
        if str(message.from_user.id) in self.superusers or await self.db_admin.check_access(str(message.from_user.id)):
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
        self.scheduler.add_job(self.__update_support_rows_for_database, 'cron', hour=1, minute=0)
        self.scheduler.start()

    async def forward_feedback(self, message: types.Message):
        """
        Method for sending feedback
        """
        logging.info(f"The user @{message.from_user.username} "
                     f"(full name: {message.from_user.full_name}) sent the file")
        if await self.db_user.get_name(message.from_user.id):
            await self.bot.forward_message(self.feedback_id_chat, message.from_user.id, message.message_id)
            await message.reply("забрал ОС✅")

    async def additional_task(self, message: types.Message):
        """
        Method of receiving a message about additional tasks and recording them
        """
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
                    await message.reply('Ошибка! Отчет не соответствует требованиям')
                except ValueError:
                    await message.reply('Ошибка! Неверный формат даты. Необходимо указать дату в 4 строке.')

    def _reg_handlers(self, dp: Dispatcher):
        """
        registration of message handlers
        """
        dp.register_message_handler(self.start, commands="start")
        dp.register_message_handler(self.get_job, text="Получить задание", state=None)
        dp.register_message_handler(self.number_of_tickets, content_types='text', state=Form.number_tickets)
        dp.register_message_handler(self.comment, content_types='text', state=Form.comment)
        dp.register_message_handler(self.unloading_from_tables, text='Выгрузка')
        dp.register_message_handler(self.priority_task, text='Приоритет', state=None)
        dp.register_message_handler(self.get_login_support, content_types='text', state=Form.logins)
        dp.register_message_handler(self.user_update, text="Обновить аудиторов")
        dp.register_message_handler(self.user_skill_update, text='Обновить навыки')
        dp.register_message_handler(self.user_info, text='Список аудиторов')
        dp.register_message_handler(self.admin_update, text='Обновить админов')
        dp.register_message_handler(self.get_log, text='Логи')
        dp.register_message_handler(self.forward_feedback, content_types=('video', 'document', 'audio'))
        dp.register_message_handler(self.additional_task, regexp="#доп_задание")

    def run(self):
        """
        bot startup
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._reg_handlers(self.dp)
        executor.start_polling(self.dp, skip_updates=True, on_startup=self.on_startup, loop=loop)
