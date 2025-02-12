import sqlite3
import hashlib
import dataclasses
from contextlib import contextmanager

from .errors import InvalidUsernameError
from ..config import DATA_HOME

def hash_password(username: str, password: str):
    return hashlib.sha256(f"{username}:{password}".encode()).hexdigest()

def validate_username(username: str) -> tuple[bool, str]:
    if not 3 <= len(username) <= 20:
        return False, "Username must be between 3 and 20 characters"
    if username == 'shared':
        return False, "Username 'shared' is reserved"
    if not username.isidentifier():
        return False, "Username must be an identifier"
    if '-' in username or ':' in username:
        return False, "Username cannot contain '-' or ':'"
    if username.startswith('_') or username.endswith('_'):
        return False, "Username cannot start or end with '_'"
    return True, ""

def check_username(username: str):
    if not (res := validate_username(username))[0]: raise InvalidUsernameError(res[1])

@dataclasses.dataclass
class UserRecord:
    userid: int
    name: str
    is_admin: bool

@dataclasses.dataclass
class UserQuota:
    userid: int
    max_pods: int
    gpu_count: int
    memory_limit: int # in GB

class UserDatabase:
    def __init__(self):

        DATA_HOME.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(DATA_HOME / "users.db", check_same_thread=False)
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
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """
            )
    
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
            print(f"User {username} added with id {res}")
    
    def update_user(self, username: str, **kwargs):
        print(f"Updating user {username} with {kwargs}")
        check_username(username)
        if 'password' in kwargs and kwargs['password'] is not None:
            with self.transaction() as c:
                c.execute("UPDATE users SET credential = ? WHERE username = ?", (hash_password(username, kwargs.pop('password')), username))
                print("Password updated")
        # if 'max_pods' in kwargs and kwargs['max_pods'] is not None:
        #     with self.transaction() as c:
        #         c.execute("UPDATE users SET max_pods = ? WHERE username = ?", (kwargs.pop('max_pods'), username))
        #         print("Max pods updated")
        if 'is_admin' in kwargs and kwargs['is_admin'] is not None:
            with self.transaction() as c:
                c.execute("UPDATE users SET is_admin = ? WHERE username = ?", (kwargs.pop('is_admin'), username))
                print("Admin status updated")
    
    def has_user(self, username: str)->bool:
        with self.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = ?", (username,))
            return cur.fetchone() is not None

    def check_user(self, credential: str):
        with self.cursor() as cur:
            cur.execute("SELECT id, username, is_admin FROM users WHERE credential = ?", (credential,))
            res = cur.fetchone()
            if res is None: return UserRecord(0, '', False)
            else: return UserRecord(*res)
    
    def delete_user(self, username: str):
        with self.transaction() as cursor:
            cursor.execute(
                "DELETE FROM users WHERE username = ?",
                (username,),
            )

    def check_user_quota(self, usrname: str):
        with self.cursor() as cur:
            cur.execute(
                "SELECT id, max_pods, gpu_count, memory_limit FROM user_quota WHERE user_id = (SELECT id FROM users WHERE username = ?)",
                (usrname,),
            )
            res = cur.fetchone()
            if res is None: return UserQuota(0, -1, -1, -1)
            else: return UserQuota(*res)

    def update_user_quota(self, usrname: str, **kwargs):
        with self.transaction() as cursor:
            if 'max_pods' in kwargs and kwargs['max_pods'] is not None:
                cursor.execute(
                    "UPDATE user_quota SET max_pods = ? WHERE user_id = (SELECT id FROM users WHERE username = ?)",
                    (kwargs.pop('max_pods'), usrname),
                )
            if 'gpu_count' in kwargs and kwargs['gpu_count'] is not None:
                cursor.execute(
                    "UPDATE user_quota SET gpu_count = ? WHERE user_id = (SELECT id FROM users WHERE username = ?)",
                    (kwargs.pop('gpu_count'), usrname),
                )
            if 'memory_limit' in kwargs and kwargs['memory_limit'] is not None:
                cursor.execute(
                    "UPDATE user_quota SET memory_limit = ? WHERE user_id = (SELECT id FROM users WHERE username = ?)",
                    (kwargs.pop('memory_limit'), usrname),
                )

    def close(self):
        self.conn.close()