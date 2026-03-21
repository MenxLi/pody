import sqlite3
import hashlib
import dataclasses
from typing import Optional, Literal

import requests
import urllib.parse
from .db import DatabaseAbstract
from .log import get_logger
from .nparse import check_name_part
from .errors import InvalidUsernameError
from ..config import DATA_HOME, config

def hash_password(username: str, password: str):
    return hashlib.sha256(f"{username}:{password}".encode()).hexdigest()

def check_username(username: str):
    if not (res := check_name_part(username, ['share']))[0]: raise InvalidUsernameError(res[1])

@dataclasses.dataclass
class UserRecord:
    userid: int
    name: str
    is_admin: bool

class UserDatabase:
    def __init__(self, mode: Literal['local', 'remote', '_auto'] = '_auto'):
        if mode == '_auto':
            if config().remote_user_profile.provider.enabled:
                mode = 'remote'
            else:
                mode = 'local'
        
        match mode:
            case 'local':
                self._impl = UserDatabase_Local()
            case 'remote':
                self._impl = UserDatabase_Remote()
            case _:
                raise ValueError(f"Invalid user database mode: {mode}")
    
    def close(self):
        self._impl.close()
    
    def __del__(self):
        self.close()
    
    def add_user(self, username: str, password: str, is_admin: bool = False) -> None:
        return self._impl.add_user(username, password, is_admin)
    
    def update_user(self, username: str, **kwargs) -> None:
        return self._impl.update_user(username, **kwargs)
    
    def delete_user(self, username: str) -> None:
        return self._impl.delete_user(username)

    def get_user(self, user_id: str | int) -> UserRecord:
        return self._impl.get_user(user_id)
    
    def check_user(self, credential: str) -> UserRecord:
        return self._impl.check_user(credential)
    
    def list_users(self, usernames: Optional[list[str]] = None) -> list[UserRecord]:
        return self._impl.list_users(usernames)

class UserDatabase_Remote:
    def __init__(self):
        self.logger = get_logger('engine')
        self._provider = config().remote_user_profile.provider
        if not self._provider.enabled:
            raise NotImplementedError("Remote user profile provider is not enabled")
        if not self._provider.access_token or not self._provider.endpoint:
            raise ValueError("Remote user profile provider is not properly configured")
        
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {self._provider.access_token}"})
    
    def close(self):
        self._session.close()
    
    def _fetch(self, method: str, path: str, query_params: dict = {}):
        base_url = self._provider.endpoint.rstrip('/') + '/user_api'
        url_raw = base_url + '/' + path.lstrip('/')
        url = url_raw + '?' + urllib.parse.urlencode(query_params)
        http_error_mapping = {
            401: (PermissionError, "Unauthorized"),
            403: (PermissionError, "Forbidden"),
            404: (LookupError, "Not found"),
            423: (RuntimeError, "Remote provider error"),
            500: (RuntimeError, "Remote provider error"),
            501: (RuntimeError, "Remote provider error"),
        }

        resp = self._session.request(method, url)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code in http_error_mapping:
            err_cls, err_msg = http_error_mapping[resp.status_code]
            raise err_cls(f"{err_msg} ({resp.status_code}): {resp.text}")
        else:
            raise RuntimeError(f"Unexpected response from remote provider ({resp.status_code}): {resp.text}")
    
    def add_user(self, username: str, password: str, is_admin: bool = False):
        self._fetch("POST", "/add_user", {"username": username, "password": password, "is_admin": is_admin})
        self.logger.info(f"Added user {username} via remote provider")
    
    def update_user(self, username: str, **kwargs):
        self._fetch("POST", "/update_user", {"username": username, **kwargs})
        self.logger.info(f"Updated user {username} via remote provider")
    
    def delete_user(self, username: str):
        self._fetch("POST", "/delete_user", {"username": username})
        self.logger.info(f"Deleted user {username} via remote provider")
    
    def get_user(self, user_id: str | int):
        raw = self._fetch("GET", "/get_user", {"user_id": user_id} if isinstance(user_id, int) else {"username": user_id})
        return UserRecord(**raw)
    
    def check_user(self, credential: str):
        raw = self._fetch("GET", "/check_user", {"credential": credential})
        return UserRecord(**raw)
    
    def list_users(self, usernames: Optional[list[str]] = None):
        raw = self._fetch("GET", "/list_users", {"usernames": ','.join(usernames)} if usernames else {})
        return [UserRecord(**u) for u in raw]

class UserDatabase_Local(DatabaseAbstract):
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

    def add_user(self, username: str, password: str, is_admin: bool = False):
        check_username(username)
        with self.transaction() as cursor:
            cursor.execute(
                "INSERT INTO users (username, credential, is_admin) VALUES (?, ?, ?)",
                (username, hash_password(username, password), is_admin),
            )
            res = cursor.lastrowid
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

    def delete_user(self, username: str):
        with self.transaction() as cursor:
            cursor.execute(
                "DELETE FROM users WHERE username = ?",
                (username,),
            )
            self.logger.info(f"User {username} deleted")
    
    def get_user(self, user_id: str | int):
        """May return UserRecord of id=0 if not found"""
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
