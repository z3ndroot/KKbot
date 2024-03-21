import asyncio
import json
import logging
import os

import aiofiles
import aiosqlite
from aiosqlite import IntegrityError
from pydantic import ValidationError

from validators import SupportCreate, UserCreate, AdminCreate


class Admin:
    def __init__(self, config):
        self.db = config['db']
        asyncio.run(self.__create_database())

    async def __create_database(self):
        """
        The method creates a database with tables user and admin
        :return:
        """
        try:
            if not os.path.isfile(self.db):
                async with aiosqlite.connect(self.db) as db:
                    await db.execute('''
                            CREATE TABLE admin
                            (login text, id int PRIMARY KEY)
                            ''')
                    await db.execute('''
                            CREATE TABLE user
                            (login text, id int PRIMARY KEY, skill text, num int)
                            ''')
                    await db.execute('''
                            CREATE TABLE task
                            (status text, date text, login text PRIMARY KEY, link text, comment text, 
                            skillsup text, skill text, output text, appreciated int, autochecks int, 
                            residue int, priority int DEFAULT 0)
                    ''')
                    await db.execute("""CREATE TABLE IF NOT EXISTS "aiogram_state"(
                                                            "user" BIGINT NOT NULL PRIMARY KEY,
                                                            "chat" BIGINT NOT NULL,
                                                            "state" TEXT NOT NULL)""")
                    await db.execute("""CREATE TABLE IF NOT EXISTS "aiogram_data"(
                                                        "user" BIGINT NOT NULL PRIMARY KEY,
                                                        "chat" BIGINT NOT NULL,
                                                        "data" TEXT)""")
                    await db.execute("""CREATE TABLE IF NOT EXISTS "aiogram_bucket"(
                                                        "user" BIGINT NOT NULL PRIMARY KEY,
                                                        "chat" BIGINT NOT NULL,
                                                        "bucket" TEXT NOT NULL)""")
                    await db.commit()
        except Exception as e:
            logging.error('An error occurred during create_database method execution: %s', e)
            raise e

    async def check_access(self, id_telegram):
        """
        Method access verification
        :param id_telegram: user id telegram
        :return:
        """
        try:
            async with aiosqlite.connect(self.db) as cursor:
                cursor_object = await cursor.execute(f"""
                                    select login from admin
                                    where id == {id_telegram}
                """)
                result = await cursor_object.fetchone()
                if result:
                    return result
        except Exception as e:
            logging.error('An error occurred during check_access method execution: %s', e)
            raise e

    async def unloading(self, rows):
        """
        Validation and writing of rows to the database
        :param rows: upload lines
        :return:
        """
        async with aiosqlite.connect(self.db) as cursor:
            await cursor.execute("DELETE from task")
            await cursor.commit()
            for row in rows:
                try:
                    support = SupportCreate.from_list(row)
                except (ValueError, ValidationError, IndexError):
                    continue
                try:
                    await cursor.execute("""
                        INSERT INTO task (status, date, login,
                         link, comment, skillsup, skill, output, 
                         appreciated, autochecks, residue)
                        VALUES (:status, :date, :login,
                         :link, :comment, :skillsup, :skill, :output, 
                         :appreciated, :autochecks, :residue)
                    """, support.model_dump())
                except IntegrityError:
                    logging.warning(f"This login: {support.login} is duplicated in the support table.")

            await cursor.commit()

    async def priority_setting(self, list_login):
        """
        Changing the priority in the database for tasks
        :param list_login:
        :return:
        """
        async with aiosqlite.connect(self.db) as cursor:
            update_priority = ""
            try:
                for i in list_login:
                    await cursor.execute(f"""
                                UPDATE task
                                SET (priority) = (1)
                                WHERE login == '{i}'
                    """)
                    await cursor.commit()
                    cursor_object = await cursor.execute(f"""
                    SELECT priority FROM task
                     WHERE login == '{i}'""")
                    priority_tuple = await cursor_object.fetchone()
                    priority = '✅' if priority_tuple else '❌'
                    update_priority += f'{i}:{priority}\n'
                return update_priority

            except Exception as e:
                logging.error('An error occurred during priority_setting method execution: %s', e)
                raise e

    async def skills_update(self, list_user):
        """
        Updating user skills
        :param list_user: User list
        :return:
        """
        try:
            async with aiosqlite.connect(self.db) as cursor:
                for i in list_user:
                    try:
                        user = UserCreate.from_list(i)
                        await cursor.execute(f"""
                                        UPDATE user
                                        SET (skill) = ('{user.skill}')
                                        where id == {user.id} 
                        """)
                    except (ValidationError, ValueError, IndexError):
                        logging.warning(f'There was a problem with {i}')
                await cursor.commit()
        except Exception as e:
            logging.error('An error occurred during output_skill_counter method execution: %s', e)
            raise e

    async def user_update(self, list_user):
        """
        Compares user lists, deletes from the database if no user is found, or adds
        :param list_user: User list
        :return:
        """
        try:
            async with aiosqlite.connect(self.db) as cursor:
                result = await cursor.execute_fetchall("""
                                        SELECT * from user
                        """)
                user_from_database = [list(i[0:3]) for i in result]
                for i in user_from_database:  # delete users
                    if i not in list_user:
                        await cursor.execute(f"""DELETE FROM user 
                                            WHERE id == {i[1]}
                        """)
                await cursor.commit()

                for i in list_user:
                    try:
                        user = UserCreate.from_list(i)
                        if i not in user_from_database:  # add new users
                            await cursor.execute("""
                                            INSERT INTO user
                                            VALUES (?,?,?,?)
                            """, (user.login, user.id, user.skill, 0))
                    except (ValidationError, ValueError, IndexError):
                        logging.warning(f'There was a problem with {i}')
                    except IntegrityError:
                        logging.warning(f"This id: {user.id} is duplicated in the google table.")
                await cursor.commit()
        except Exception as e:
            logging.error('An error occurred during user_update method execution: %s', e)
            raise e

    async def get_user_from_database(self):
        """
        Uploads all users to a separate json file
        :return:
        """
        try:
            async with aiosqlite.connect(self.db) as cursor:
                users = await cursor.execute_fetchall("""
                                        SELECT * from user
                            """)
                result = {"Users": users}
                async with aiofiles.open('db/user.json', 'w', encoding="UTF8") as file:
                    await file.write(json.dumps(result, indent=4, ensure_ascii=False))
        except Exception as e:
            logging.error('An error occurred during get_user_from_database method execution: %s', e)
            raise e

    async def admin_update(self, list_admin):
        """
        Compares lists of admin, removes from the database if no admin is found or adds.
        :param list_admin: User list
        :return:
        """
        try:
            async with aiosqlite.connect(self.db) as cursor:
                result = await cursor.execute_fetchall("""
                                        SELECT * from admin
                        """)
                admin_from_database = [list(i) for i in result]
                for i in admin_from_database:  # delete admin
                    if i not in list_admin:
                        await cursor.execute(f"""
                                        DELETE FROM admin
                                        WHERE id == {i[1]}
                        """)
                await cursor.commit()

                for i in list_admin:
                    try:
                        admin = AdminCreate.from_list(i)
                        if i not in admin_from_database:  # add new admin
                            await cursor.execute("""
                                            INSERT INTO admin
                                            VALUES (?,?)
                            """, (admin.login, admin.id))
                    except (ValidationError, ValueError, IndexError):
                        logging.warning(f'There was a problem with {i}')
                await cursor.commit()
        except Exception as e:
            logging.error('An error occurred during admin_update method execution: %s', e)
            raise e
