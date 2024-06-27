from aiogram.types import (KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                           InlineKeyboardMarkup, InlineKeyboardButton)


class Localized:
    """
    test
    """
    def __init__(self):
        self.buttons = {
            'ru': {
                "button_comment": [
                    KeyboardButton('нет тикетов'),
                    KeyboardButton('нет смен'),
                    KeyboardButton('уволен'),
                    KeyboardButton('больничный'),
                    KeyboardButton('отпуск/обс'),
                ],
                'get_task_butt': [
                    KeyboardButton('Получить задание')
                ],
                'button_cancel': [
                    KeyboardButton('Отмена')
                ],
                "button_change": [
                    InlineKeyboardButton(text='Изменить', callback_data='change')
                ],
                "admin_button": [
                    KeyboardButton('Обновить навыки'),
                    KeyboardButton('Обновить админов'),
                    KeyboardButton('Обновить аудиторов'),
                    KeyboardButton('Список аудиторов'),
                    KeyboardButton('Приоритет'),
                    KeyboardButton('Выгрузка'),
                    KeyboardButton('Логи'),
                ]
            },
            'en': {
                "button_comment": [
                    KeyboardButton('No Tickets'),
                    KeyboardButton('No Shifts'),
                    KeyboardButton('Fired'),
                    KeyboardButton('Sick Leave'),
                    KeyboardButton('Vacation/OBS'),
                ],
                'get_task_butt': [
                    KeyboardButton('Get Task')
                ],
                'button_cancel': [
                    KeyboardButton('Cancel')
                ],
                "button_change": [
                    InlineKeyboardButton(text='Change', callback_data='change')
                ],
                "admin_button": [
                    KeyboardButton('Update Skills'),
                    KeyboardButton('Update Admins'),
                    KeyboardButton('Update Auditors'),
                    KeyboardButton('List of Auditors'),
                    KeyboardButton('Priority'),
                    KeyboardButton('Unload'),
                    KeyboardButton('Logs'),
                ]
            }
        }
        self.messages = {
            "ru": {
                "hello": "Привет",
                "count_tickets": "Введи кол-во оценённых тикетов:",
                "comment": "⚠Напишите комментарий к агенту⚠:",
                "waiting": "⏱Пожалуйста подождите.....",
                "count_rec": "Количество записано✅",
                "error_int": "Ответ должно содержать целое число!!!",
                "comment_rec": "Комментарий записан✅",
                "change_count": "Ведите кол-во тикетов для исправления",
                "info_old_task": "Задача устарела. Обратись к РГ для исправления👨🏾‍🦳",
                "waiting_change": "Вычисляю...🤖",
                "info_empty_entry": "Не удалось найти запись в таблице. Обратитесь к РГ",
                "info_error_entry": "При записи возникла ошибка. Попробуйте еще раз немного позднее",
                "success_change": "Изменения успешно внесены✅",
                "reset_change": "Изменения отменены🙅",
                "wrong_count_ticket": "❌Проверьте правильность кол-во тикетов и введите его заново",
                "unloading_wait": "⏱Выгрузка. Пожалуйста подождите.....",
                "success_unloading": "Выгрузка обновлена✅",
                "send_login": "Отправь мне список логинов в формате:\ntest\ntest2\ntest3",
                "result_prior": "Результаты обновления приоритета:",
                "update_db": "База данных обновлена✅",
                "update_db_root": "База данных Администраторов обновлена✅",
                "get_oc": "забрал ОС✅",
                "wrong_add_task": "Ошибка! Отчет не соответствует требованиям",
                "wrong_date_task": "Ошибка! Неверный формат даты. Необходимо указать дату в 4 строке."
            },

            "en": {
                "hello": "Hi",
                "count tickets": "Enter the number of assessed tickets:",
                "comment": "⚠Write a comment to the agent⚠:",
                "waiting": "⏱Please wait.....",
                "count_rec": "Count recorded✅",
                "error_int": "Response must contain an integer!!!",
                "comment_rec": "Comment recorded✅",
                "change_count": "Enter the number of tickets to correct",
                "info_old_task": "The task is outdated. Contact RG for correction👨🏾‍🦳",
                "waiting_change": "Calculating...🤖",
                "info_empty_entry": "No entry found in the table. Contact RG",
                "info_error_entry": "An error occurred while writing. Please try again later",
                "success_change": "Changes successfully made✅",
                "reset_change": "Changes canceled🙅",
                "wrong_count_ticket": "❌Check the correctness of the ticket count and enter it again",
                "unloading_wait": "⏱Unloading. Please wait.....",
                "success_unloading": "Unloading updated✅",
                "send_login": "Send me a list of logins in the format:\ntest\ntest2\ntest3",
                "result_prior": "Priority update results:",
                "update_db": "Database updated✅",
                "update_db_root": "Administrators database updated✅",
                "get_oc": "picked up OC✅",
                "wrong_add_task": "Error! Report does not meet requirements",
                "wrong_date_task": "Error! Incorrect date format. Please specify the date in the 4th line."
            }
        }

    def get_keyboard(self, keyboard_key: str, current_lang: str):
        """
        Get keyboard object based on the current language setting
        """
        lang_code = current_lang
        if lang_code in self.buttons and keyboard_key in self.buttons[lang_code]:
            if keyboard_key == "admin_button":
                keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
                admin_buttons = self.buttons[lang_code][keyboard_key]
                keyboard.add(admin_buttons[0]).insert(admin_buttons[1])
                keyboard.add(admin_buttons[2]).insert(admin_buttons[3])
                keyboard.add(admin_buttons[4]).add(admin_buttons[5]).add(admin_buttons[6])
            elif keyboard_key == "button_change":
                keyboard = InlineKeyboardMarkup(row_width=4)
                keyboard.add(*self.buttons[lang_code][keyboard_key])
            else:
                keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
                keyboard.add(*self.buttons[lang_code][keyboard_key])
        else:
            keyboard = None

        return keyboard

    def get_message(self, message_key: str, current_lang: str):
        """
        Get message object based on the current language setting
        """
        lang_code = current_lang
        if lang_code in self.messages and message_key in self.messages[lang_code]:
            return self.messages[lang_code][message_key]

        return "Empty message"
