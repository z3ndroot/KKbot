from typing import Union, Dict, Optional, List, Tuple, AnyStr

import aiosqlite
import jsonpickle
from aiogram.dispatcher.storage import BaseStorage


class SQLiteStorage(BaseStorage):
    """
    AioSqlite-based storage for FSM.

    Usage:

    storage = SQLiteStorage(db_path='data/database.db')
    dp = Dispatcher(bot, storage=storage)
    """

    def __init__(self, db_path):
        self._path_db = db_path
        self._db = None

    async def close(self):
        if isinstance(self._db, aiosqlite.Connection):
            await self._db.close()

    async def get_db(self) -> aiosqlite.Connection:
        if isinstance(self._db, aiosqlite.Connection):
            return self._db

        self._db = await aiosqlite.connect(database=self._path_db)

        return self._db

    async def wait_closed(self):
        return True

    async def set_state(self, *, chat: Union[str, int, None] = None,
                        user: Union[str, int, None] = None,
                        state: Optional[AnyStr] = None):
        chat, user = map(int, self.check_address(chat=chat, user=user))
        db = await self.get_db()

        if state is not None:
            await db.execute("""INSERT INTO "aiogram_state" VALUES(?, ?, ?)"""
                             """ON CONFLICT ("user") DO UPDATE SET "state" = ?""",
                             (user, chat, self.resolve_state(state), self.resolve_state(state)))
            await db.commit()
        else:
            await db.execute("""DELETE FROM "aiogram_state" WHERE chat=? AND "user"=?""", (chat, user))
            await db.commit()

    async def get_state(self, *, chat: Union[str, int, None] = None, user: Union[str, int, None] = None,
                        default: Optional[str] = None) -> Optional[str]:
        chat, user = map(int, self.check_address(chat=chat, user=user))
        db = await self.get_db()
        async with db.execute("""SELECT "state" FROM "aiogram_state" WHERE "chat"=? AND "user"=?""",
                              (chat, user)) as cursor:
            result = await cursor.fetchone()
        return result[0] if result else self.resolve_state(default)

    async def set_data(self, *, chat: Union[str, int, None] = None, user: Union[str, int, None] = None,
                       data: Dict = None):
        chat, user = map(int, self.check_address(chat=chat, user=user))
        db = await self.get_db()

        if data:
            await db.execute("""INSERT INTO "aiogram_data" VALUES(?, ?, ?)"""
                             """ON CONFLICT ("user") DO UPDATE SET "data" = ?""",
                             (user, chat, jsonpickle.encode(data), jsonpickle.encode(data)))
            await db.commit()
        else:
            await db.execute("""DELETE FROM "aiogram_data" WHERE "chat"=? AND "user"=?""", (chat, user))
            await db.commit()

    async def get_data(self, *, chat: Union[str, int, None] = None, user: Union[str, int, None] = None,
                       default: Optional[dict] = None) -> Dict:
        chat, user = map(int, self.check_address(chat=chat, user=user))
        db = await self.get_db()
        async with db.execute("""SELECT "data" FROM "aiogram_data" WHERE "chat"=? AND "user"=?""",
                              (chat, user)) as cursor:
            result = await cursor.fetchone()

        return jsonpickle.decode(result[0]) if result else default or {}

    async def update_data(self, *, chat: Union[str, int, None] = None, user: Union[str, int, None] = None,
                          data: Dict = None, **kwargs):
        if data is None:
            data = {}
        temp_data = await self.get_data(chat=chat, user=user, default={})
        temp_data.update(data, **kwargs)
        await self.set_data(chat=chat, user=user, data=temp_data)

    def has_bucket(self):
        return True

    async def get_bucket(self, *, chat: Union[str, int, None] = None, user: Union[str, int, None] = None,
                         default: Optional[dict] = None) -> Dict:
        chat, user = map(int, self.check_address(chat=chat, user=user))
        db = await self.get_db()
        async with db.execute("""SELECT "bucket" FROM "aiogram_bucket" WHERE "chat"=? AND "user"=?""",
                              (chat, user)) as cursor:
            result = await cursor.fetchone()
        return jsonpickle.decode(result[0]) if result else default or {}

    async def set_bucket(self, *, chat: Union[str, int, None] = None, user: Union[str, int, None] = None,
                         bucket: Dict = None):
        chat, user = map(int, self.check_address(chat=chat, user=user))
        db = await self.get_db()
        await db.execute("""INSERT INTO "aiogram_bucket" VALUES(?, ?, ?)"""
                         """ON CONFLICT ("user") DO UPDATE SET "bucket" = ?""",
                         (user, chat, jsonpickle.encode(bucket), jsonpickle.encode(bucket)))
        await db.commit()

    async def update_bucket(self, *, chat: Union[str, int, None] = None,
                            user: Union[str, int, None] = None,
                            bucket: Dict = None, **kwargs):
        if bucket is None:
            bucket = {}
        temp_bucket = await self.get_bucket(chat=chat, user=user)
        temp_bucket.update(bucket, **kwargs)
        await self.set_bucket(chat=chat, user=user, bucket=temp_bucket)

    async def reset_all(self, full=True):
        db = await self.get_db()
        await db.execute("DROP TABLE aiogram_state")
        if full:
            await db.execute("DROP TABLE aiogram_data")
            await db.execute("DROP TABLE aiogram_bucket")

        await db.commit()

    async def get_states_list(self) -> List[Tuple[int, int]]:
        db = await self.get_db()
        async with db.execute("SELECT * FROM aiogram_state") as cursor:
            items = await cursor.fetchall()
        return [(int(item[1]), int(item[0])) for item in items]
