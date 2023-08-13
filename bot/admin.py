import aiosqlite
import logging


class Admin:
    def __init__(self, config):
        self.db = config['db']

    async def check_access(self, id_telegram):
        """
        Method access verification
        :param id_telegram: user id telegram
        :return:
        """
        async with aiosqlite.connect(self.db) as cursor:
            cursor_object = await cursor.execute(f"""
                                select login from admin
                                where id == {id_telegram}
            """)
            result = await cursor_object.fetchone()
            if result:
                return result
            else:
                logging.warning('Admin %s was not found', id_telegram)
