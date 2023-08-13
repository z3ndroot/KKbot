import aiosqlite
import logging
import aiofiles
import json


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
                result = await cursor.execute_fetchall("""
                                                    SELECT * from user
                """)
                user_from_database = [list(i[0:3]) for i in result]
                for i in list_user:
                    if i not in user_from_database:  # update skills
                        await cursor.execute(f"""
                                        UPDATE user
                                        SET (skill) = ('{i[2]}')
                                        where id == {i[1]} 
                        """)
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
                for i in list_user:
                    if i not in user_from_database:  # add new users
                        await cursor.execute(f"""
                                        INSERT INTO user
                                        VALUES ('{i[0]}','{i[1]}','{i[2]}','0')
                                           
                        """)
                await cursor.commit()

                for i in user_from_database:  # delete users
                    if i not in list_user:
                        await cursor.execute(f"""DELETE FROM user 
                                            WHERE id == {i[1]}
                        """)
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
                print(admin_from_database)
                for i in list_admin:
                    if i not in admin_from_database:  # add new admin
                        await cursor.execute(f"""
                                        INSERT INTO admin
                                        VALUES ('{i[0]}','{i[1]}')
                        """)
                await cursor.commit()

                for i in admin_from_database:  # delete admin
                    if i not in list_admin:
                        print(i)
                        await cursor.execute(f"""
                                        DELETE FROM admin
                                        WHERE id == {i[1]}
                        """)
                await cursor.commit()
        except Exception as e:
            logging.error('An error occurred during admin_update method execution: %s', e)
            raise e
