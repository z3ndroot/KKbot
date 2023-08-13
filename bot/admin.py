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

    async def skills_update(self, list_user):
        """
        Updating user skills
        :param list_user: User list
        :return:
        """
        try:
            async with aiosqlite.connect(self.db) as cursor:
                for i in list_user:
                    await cursor.execute(f"""
                                    UPDATE user
                                    SET (skill) = ('{i[2]}')
                                    where id == {i[1]} 
                    """)
                await cursor.commit()
        except Exception as e:
            logging.error('An error occurred during output_skill_counter method execution: %s', e)
            raise e
