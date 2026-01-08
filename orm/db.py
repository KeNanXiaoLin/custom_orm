import sqlite3
from typing import Any, List, Dict, Optional


class Database:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self._connection = None
        self._cursor = None
    
    def connect(self):
        self._connection = sqlite3.connect(self.db_url)
        self._connection.row_factory = sqlite3.Row
        self._cursor = self._connection.cursor()
    
    def close(self):
        if self._cursor:
            self._cursor.close()
            self._cursor = None
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._connection.rollback()
        else:
            self._connection.commit()
        self.close()
    
    def execute(self, sql: str, params: Optional[tuple] = None) -> sqlite3.Cursor:
        if not self._cursor:
            raise RuntimeError("Database connection not established")
        return self._cursor.execute(sql, params or ())
    
    def fetch_one(self, sql: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        cursor = self.execute(sql, params)
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def fetch_all(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        cursor = self.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def commit(self):
        if not self._connection:
            raise RuntimeError("Database connection not established")
        self._connection.commit()
    
    def rollback(self):
        if not self._connection:
            raise RuntimeError("Database connection not established")
        self._connection.rollback()
    
    def get_cursor(self) -> sqlite3.Cursor:
        if not self._cursor:
            raise RuntimeError("Database connection not established")
        return self._cursor
