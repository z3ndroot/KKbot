import asyncio
import json
import logging

import aiofiles
from aiogram import Bot
from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils import executor

from admin import Admin
from google_sheet import SheetGoogle
from user import User


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
            KeyboardButton('Выгрузка'),
            KeyboardButton('Список аудиторов'),
            KeyboardButton('Обновить аудиторов'),
            KeyboardButton('Обновить навыки'),
            KeyboardButton('Обновить админов'),
            KeyboardButton('Ошибки'),
            KeyboardButton('Обновить группы'),
            KeyboardButton('Список групп'),
            KeyboardButton('Изменить строку'),
        ]
        self.buttons_comment = ReplyKeyboardMarkup(resize_keyboard=True)
        self.buttons_comment.add(*self.button_comment)
        self.get_task = ReplyKeyboardMarkup(resize_keyboard=True)
        self.get_task.add(self.get_task_butt)
        self.admin_buttons = ReplyKeyboardMarkup(resize_keyboard=True)
        self.admin_buttons.add(*self.admin_button)

    async def start(self, message: types.Message):
        """
        Method of processing the start command
        """
        logging.info(f'The /start command from user: {message.from_user.full_name} || @{message.from_user.username}')
        if str(message.from_user.id) in self.superusers or await self.db_admin.check_access(str(message.from_user.id)):
            await message.reply(f"Привет, {message.from_user.first_name}", reply_markup=self.admin_buttons)
        elif await self.db_user.get_name(str(message.from_user.id)):
            await message.reply(f"Привет, {message.from_user.first_name}", reply_markup=self.get_task)

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

    def run(self):
        """
        bot startup
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._reg_handlers(self.dp)
        executor.start_polling(self.dp, skip_updates=True, loop=loop)
