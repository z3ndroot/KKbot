import aiosqlite
import logging


class User:
    def __init__(self, config):
        self.db = config['db']

    async def skill_read(self, id_telegram):
        """
        Getting skills from the database
        :param id_telegram: user id telegram
        :return: list of user skills
        """
        async with aiosqlite.connect(self.db) as cursor:
            result = await cursor.execute_fetchall(f"""
                                SELECT skill FROM user
                                WHERE id== {id_telegram}
            """)
            skill_kk = list(*result)

            return skill_kk

    async def get_name(self, id_telegram):
        """
        Method for obtaining username and also access verification
        :param id_telegram: user id telegram
        :return: username
        """
        async with aiosqlite.connect(self.db) as cursor:
            cursor_object = await cursor.execute(f"""
                                select login from user
                                where id == {id_telegram}
            """)
            result = await cursor_object.fetchone()
            if result:
                return result[0]
            else:
                logging.info('User %s was not found', id_telegram)