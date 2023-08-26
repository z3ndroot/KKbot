# KKbot Telegram

![python-version](https://img.shields.io/badge/python-3.11.4-yellow)
[![aiogram-version](https://img.shields.io/badge/aiogram-2.25.1-green
)](https://aiogram.dev/)
[![aiosqlite-version](https://img.shields.io/badge/aiosqlite-0.19.0-red
)](https://aiosqlite.omnilib.dev/en/stable/)
[![pydantic-version](https://img.shields.io/badge/pydantic-2.2.1-white
)](https://docs.pydantic.dev/latest/)
[![gspread-version](https://img.shields.io/badge/gspread_asyncio-1.9.0-blue
)](https://gspread-asyncio.readthedocs.io/en/latest/)

This is a Telegram bot for distributing tasks among quality control employees and recording completed tasks in Google Sheets. The project uses the aiogram, gspread, aiosqlite, and pydantic libraries.

## Installation

Clone the repository and navigate to the project directory:

```
git clone https://github.com/z3ndroot/KKbot
cd KKbot
```

#### From Source

1. Create a virtual environment:

```
python -m venv venv
```

2. Activate the virtual environment:

```
# For Linux or macOS:
source venv/bin/activate

# For Windows:
venv\Scripts\activate
```

3. Install dependencies using the requirements.txt file:

```
pip install -r requirements.txt
```

4. Run the bot with the following command:

```
python bot/main.py
```

## Parameters .env

### Google Sheet

| Parameter             | Description |
|----------------------|-------------|
| SPREADSHEET_ID      | The ID of the Google Sheets table where information will be recorded |
| TASK_SHEET_NAME     | The name of the sheet on Google Sheets where tasks are recorded |
| TASK_BEGIN_COLUMN   | The starting column number for recording |
| USER_SHEET_NAME     | The name of the sheet on Google Sheets with the list of users |
| ADMIN_SHEET_NAME    | The name of the sheet on Google Sheets with the list of administrators |
| ADDITION_SHEET_NAME | The name of the sheet on Google Sheets with the list of additional tasks |
| ADDITION_BEGIN_COLUMN| The starting column number for recording additional tasks |

### DB

| Parameter   | Description           |
|------------|-----------------------|
| DB_PATH  | The path to the SQLite database file |

### Telegram Bot

| Parameter         | Description                                                     |
|------------------|-----------------------------------------------------------------|
| TOKEN_TELEGRAM  | The token of the Telegram bot to be used for work |
| SUPERUSER       | The list of Telegram user IDs that will be considered superusers and will have access to all bot functions |
| FEEDBACK_ID     | The Telegram chat ID where feedback messages will be sent |
| ADDITIONAL_ID   | The Telegram chat ID from which additional tasks will be uploaded. The chat must be created separately. |

## Administrator Functions

Additional functions are available for administrators in the bot that allow them to:

- Update skills for employees
- Update lists of administrators and employees
- Set priority for a specific task
- Upload new tasks
- View bot work logs

To access the administrator buttons, you must be on the list of administrators.

Each button is intended to simplify work with the bot and edit information about tasks, employees, and administrators.