import aiosqlite


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
