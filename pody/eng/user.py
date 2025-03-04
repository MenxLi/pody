import sqlite3
import hashlib
import dataclasses
from typing import Optional
from contextlib import contextmanager
from abc import ABC, abstractmethod

from .log import get_logger
from .errors import InvalidUsernameError
from .utils import format_storage_size
from ..config import DATA_HOME, validate_name_part

def hash_password(username: str, password: str):
    return hashlib.sha256(f"{username}:{password}".encode()).hexdigest()

def check_username(username: str):
    if not (res := validate_name_part(username, ['share']))[0]: raise InvalidUsernameError(res[1])

@dataclasses.dataclass
class UserRecord:
    userid: int
    name: str
    is_admin: bool

class DatabaseAbstract(ABC):

    @property
    @abstractmethod
    def conn(self) -> sqlite3.Connection:
        ...

    def cursor(self):
        @contextmanager
        def _cursor():
            cursor = self.conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()
        return _cursor()
    
    def transaction(self):
        @contextmanager
        def _transaction():
            cursor = self.conn.cursor()
            try:
                cursor.execute("BEGIN")
                yield cursor
            except Exception as e:
                cursor.execute("ROLLBACK")
                raise e
            else:
                self.conn.commit()
            finally:
                cursor.close()
        return _transaction()

    def close(self):
        self.conn.close()

class UserDatabase(DatabaseAbstract):
    @property
    def conn(self): return self._conn
    def __init__(self):
        self.logger = get_logger('engine')

        DATA_HOME.mkdir(exist_ok=True)
        self._conn = sqlite3.connect(DATA_HOME / "users.db", check_same_thread=False)
        # enable foreign key constraint
        self.conn.execute("PRAGMA foreign_keys = ON;")

        with self.transaction() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    credential TEXT NOT NULL, 
                    is_admin BOOLEAN NOT NULL DEFAULT 0
                );
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_quota (
                    user_id INTEGER PRIMARY KEY,
                    max_pods INTEGER NOT NULL DEFAULT -1,
                    gpu_count INTEGER NOT NULL DEFAULT -1,
                    memory_limit INTEGER NOT NULL DEFAULT -1,
                    storage_limit INTEGER NOT NULL DEFAULT -1,
                    shm_size INTEGER NOT NULL DEFAULT -1,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """
            )
        self.auto_upgrade()

    def auto_upgrade(self):
        # add missing columns
        with self.transaction() as cursor:
            cursor.execute("PRAGMA table_info(user_quota)")
            cols = cursor.fetchall()
            if not any([col[1] == 'storage_limit' for col in cols]):
                cursor.execute("ALTER TABLE user_quota ADD COLUMN storage_limit INTEGER NOT NULL DEFAULT -1")
            if not any([col[1] == 'shm_size' for col in cols]):
                cursor.execute("ALTER TABLE user_quota ADD COLUMN shm_size INTEGER NOT NULL DEFAULT -1")
    
    def add_user(self, username: str, password: str, is_admin: bool = False):
        check_username(username)
        with self.transaction() as cursor:
            cursor.execute(
                "INSERT INTO users (username, credential, is_admin) VALUES (?, ?, ?)",
                (username, hash_password(username, password), is_admin),
            )
            res = cursor.lastrowid
            cursor.execute(
                "INSERT INTO user_quota (user_id) VALUES (?)",
                (res,),
            )
            self.logger.info(f"User {username} added with id {res}")
    
    def update_user(self, username: str, **kwargs):
        check_username(username)
        if 'password' in kwargs and kwargs['password'] is not None:
            with self.transaction() as c:
                c.execute("UPDATE users SET credential = ? WHERE username = ?", (hash_password(username, kwargs.pop('password')), username))
                self.logger.info(f"User {username} password updated")
        if 'is_admin' in kwargs and kwargs['is_admin'] is not None:
            with self.transaction() as c:
                c.execute("UPDATE users SET is_admin = ? WHERE username = ?", (kwargs.pop('is_admin'), username))
                self.logger.info(f"User {username} is_admin updated") # to fix
    
    def has_user(self, username: str)->bool:
        with self.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = ?", (username,))
            return cur.fetchone() is not None
    
    def get_user(self, user_id: str | int):
        if isinstance(user_id, str):
            with self.cursor() as cur:
                cur.execute("SELECT id, username, is_admin FROM users WHERE username = ?", (user_id,))
                res = cur.fetchone()
                if res is None: return UserRecord(0, '', False)
                else: return UserRecord(*res)
        else:
            with self.cursor() as cur:
                cur.execute("SELECT id, username, is_admin FROM users WHERE id = ?", (user_id,))
                res = cur.fetchone()
                if res is None: return UserRecord(0, '', False)
                else: return UserRecord(*res)

    def check_user(self, credential: str):
        with self.cursor() as cur:
            cur.execute("SELECT id, username, is_admin FROM users WHERE credential = ?", (credential,))
            res = cur.fetchone()
            if res is None: return UserRecord(0, '', False)
            else: return UserRecord(*res)
    
    def list_users(self, usernames: Optional[list[str]] = None):
        if usernames is None:
            with self.cursor() as cur:
                cur.execute("SELECT id, username, is_admin FROM users")
                return [UserRecord(*u) for u in cur.fetchall()]
        else:
            with self.cursor() as cur:
                cur.execute(f"SELECT id, username, is_admin FROM users WHERE username IN ({','.join(['?']*len(usernames))})", usernames)
                return [UserRecord(*u) for u in cur.fetchall()]

    def delete_user(self, username: str):
        with self.transaction() as cursor:
            cursor.execute(
                "DELETE FROM users WHERE username = ?",
                (username,),
            )
            self.logger.info(f"User {username} deleted")

@dataclasses.dataclass
class UserQuota:
    max_pods: int
    gpu_count: int
    memory_limit: int # in bytes (per container)
    storage_limit: int # in bytes (per container, exclude external volumes)
    shm_size: int # in bytes (per container)

    def __str__(self):
        return  f"Quota(max_pods={self.max_pods}, gpu_count={self.gpu_count}, "\
                f"memory_limit={format_storage_size(self.memory_limit) if self.memory_limit >= 0 else self.memory_limit}, "\
                f"storage_limit={format_storage_size(self.storage_limit) if self.storage_limit >= 0 else self.storage_limit})"\
                f"shm_size={format_storage_size(self.shm_size) if self.shm_size >= 0 else self.shm_size})"


class QuotaDatabase(DatabaseAbstract):
    @property
    def conn(self): return self._conn
    def __init__(self):
        self.logger = get_logger('engine')

        DATA_HOME.mkdir(exist_ok=True)
        self._conn = sqlite3.connect(DATA_HOME / "quota.db", check_same_thread=False)

        with self.transaction() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS quota (
                    username TEXT PRIMARY KEY,
                    max_pods INTEGER NOT NULL DEFAULT -1,
                    gpu_count INTEGER NOT NULL DEFAULT -1,
                    memory_limit INTEGER NOT NULL DEFAULT -1,
                    storage_limit INTEGER NOT NULL DEFAULT -1,
                    shm_size INTEGER NOT NULL DEFAULT -1
                );
                """
            )
    
    def delete_quota(self, usrname: str):
        with self.transaction() as cursor:
            r = cursor.execute(
                "DELETE FROM quota WHERE username = ?",
                (usrname,),
            )
            if r.rowcount:
                self.logger.info(f"Quota for user {usrname} deleted")
            else:
                self.logger.debug(f"Skip deleting quota for user {usrname}, not found")

    def check_quota(self, usrname: str):
        with self.cursor() as cur:
            cur.execute(
                "SELECT max_pods, gpu_count, memory_limit, storage_limit, shm_size FROM quota WHERE username = ?",
                (usrname,),
            )
            res = cur.fetchone()
            if res is None: return UserQuota(-1, -1, -1, -1, -1)
            else: return UserQuota(*res)

    def update_quota(self, usrname: str, **kwargs):
        """
        Update user quota, 
        will create a new record if not exists, update the record if exists
        """
        with self.transaction() as cursor:
            r = cursor.execute(
                "INSERT OR IGNORE INTO quota (username) VALUES (?)",
                (usrname,),
            )
            if r.rowcount != 0:
                self.logger.debug(f"Quota for user {usrname} initialized")

        with self.transaction() as cursor:
            if 'max_pods' in kwargs and kwargs['max_pods'] is not None:
                cursor.execute(
                    "UPDATE quota SET max_pods = ? WHERE username = ?",
                    (kwargs.pop('max_pods'), usrname),
                )
                self.logger.info(f"User {usrname} max_pods updated")
            if 'gpu_count' in kwargs and kwargs['gpu_count'] is not None:
                cursor.execute(
                    "UPDATE quota SET gpu_count = ? WHERE username = ?",
                    (kwargs.pop('gpu_count'), usrname),
                )
                self.logger.info(f"User {usrname} gpu_count updated")
            if 'memory_limit' in kwargs and kwargs['memory_limit'] is not None:
                cursor.execute(
                    "UPDATE quota SET memory_limit = ? WHERE username = ?",
                    (kwargs.pop('memory_limit'), usrname),
                )
                self.logger.info(f"User {usrname} memory_limit updated")
            if 'storage_limit' in kwargs and kwargs['storage_limit'] is not None:
                cursor.execute(
                    "UPDATE quota SET storage_limit = ? WHERE username = ?",
                    (kwargs.pop('storage_limit'), usrname),
                )
                self.logger.info(f"User {usrname} storage_limit updated")
            if 'shm_size' in kwargs and kwargs['shm_size'] is not None:
                cursor.execute(
                    "UPDATE quota SET shm_size = ? WHERE username = ?",
                    (kwargs.pop('shm_size'), usrname),
                )
                self.logger.info(f"User {usrname} shm_size updated")
