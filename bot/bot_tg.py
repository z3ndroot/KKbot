import asyncio
import json
import logging
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
            KeyboardButton('Ошибки'),
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
        logging.info(f'The /start command from user: {message.from_user.full_name} || @{message.from_user.username}')
        if str(message.from_user.id) in self.superusers or await self.db_admin.check_access(str(message.from_user.id)):
            await message.reply(f"Привет, {message.from_user.first_name}", reply_markup=self.admin_buttons)
        elif await self.db_user.get_name(str(message.from_user.id)):
            await message.reply(f"Привет, {message.from_user.first_name}", reply_markup=self.get_task)

    async def get_job(self, message: types.Message, state: FSMContext):
        """
        Method for sending a message with information about the support
        """
        logging.info(f"Request for an assignment from {message.from_user.full_name} || @{message.from_user.username}")

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
                    'comment': '',
                }
                await self.bot.send_message(message.from_user.id, text=finished_form, parse_mode='HTML')
                logging.info(f"Task successfully completed {task[2]} for {message.from_user.full_name} || "
                             f"@{message.from_user.username}")
                await Form.number_tickets.set()
                await self.bot.send_message(message.from_user.id, "Введи кол-во оценённых тикетов:",
                                            reply_markup=ReplyKeyboardRemove())
                async with state.proxy() as data:
                    data['data_dict'] = data_dict

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

    def _reg_handlers(self, dp: Dispatcher):
        """
        registration of message handlers
        """
        dp.register_message_handler(self.start, commands="start")
        dp.register_message_handler(self.get_job, text="Получить задание", state=None)

    def run(self):
        """
        bot startup
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._reg_handlers(self.dp)
        executor.start_polling(self.dp, skip_updates=True, loop=loop)
