import aiosqlite
import logging


class User:
    def __init__(self, config):
        self.db = config['db']

    async def __skill_read(self, id_telegram):
        """
        Getting skills from the database
        :param id_telegram: user id telegram
        :return: list of user skills
        """
        async with aiosqlite.connect(self.db) as cursor:
            cursor_object = await cursor.execute(f"""
                                SELECT skill FROM user
                                WHERE id== {id_telegram}
            """)
            result = await cursor_object.fetchone()
            if result:
                return result[0].split(', ')
            else:
                logging.warning('User %s was not found and no active skills', id_telegram)

    async def get_name(self, id_telegram):
        """
        Method for obtaining username and also access verification
        :param id_telegram: user id telegram
        :return: username
        """
        try:
            async with aiosqlite.connect(self.db) as cursor:
                cursor_object = await cursor.execute(f"""
                                    select login from user
                                    where id == {id_telegram}
                """)
                result = await cursor_object.fetchone()
                if result:
                    return result[0]
        except Exception as e:
            logging.error('An error occurred during get_name method execution: %s', e)
            raise e

    async def get_support_line(self, id_telegram):
        """
        Get a skill task
        :param id_telegram: user id telegram
        :return:
        """
        skill = await self.output_skill_counter(id_telegram)
        async with aiosqlite.connect(self.db) as cursor:
            cursor_object = await cursor.execute(f"""
                SELECT * FROM task 
                WHERE skill='{skill}' 
                ORDER BY priority DESC, residue DESC LIMIT 1;
            """)
            result = await cursor_object.fetchone()
            if not result:
                return f"Нет активных задач по навыку {skill}("
            await cursor.execute(f"""
                            DELETE FROM task
                            WHERE login == '{result[2]}'
            """)
            await cursor.commit()

            return result

    async def output_skill_counter(self, id_telegram):
        """
        The method gets a counter from the database and checks it by condition, incrementing or zeroing it.
        Returns the skill that will be used
        :param id_telegram: user id telegram
        :return: skill
        """
        try:
            list_skill = await self.__skill_read(id_telegram)
            async with aiosqlite.connect(self.db) as cursor:
                cursor_object = await cursor.execute(f"""
                                    select num from user
                                    where id == {id_telegram}
                """)
                result = await cursor_object.fetchone()
                counter = result[0]

                if len(list_skill) - 1 > int(counter):
                    counter += 1
                else:
                    counter = 0

                await cursor.execute(f"""
                                    UPDATE user
                                    SET (num) = ('{counter}')
                                     where id == {id_telegram} 
                """)

                await cursor.commit()

            return list_skill[counter]
        except Exception as e:
            logging.error('An error occurred during output_skill_counter method execution: %s', e)
            raise e
