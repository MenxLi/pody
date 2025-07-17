from abc import ABC, abstractmethod
import sqlite3
from contextlib import contextmanager

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

    def __del__(self):
        self.close()