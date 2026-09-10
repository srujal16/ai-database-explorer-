"""
query_builder.py
Turns a parsed intent (from nlu_engine.parse) into a safe, parameterized
SQL query, executes it against the SQLite database, and returns results.
"""

import sqlite3

SCHEMA_COLUMNS = {
    "employees": ["id", "name", "department", "salary", "hire_date", "email"],
    "departments": ["id", "name", "location"],
    "products": ["id", "name", "category", "price", "stock"],
}

DEFAULT_FILTER_COLUMN = {
    "employees": "name",
    "departments": "name",
    "products": "price",
}


class QueryError(Exception):
    pass


class QueryBuilder:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def list_tables(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cur.fetchall()]
        conn.close()
        return tables

    def describe_table(self, table: str):
        if table not in SCHEMA_COLUMNS:
            raise QueryError(f"Unknown table '{table}'.")
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        info = cur.fetchall()  # (cid, name, type, notnull, dflt_value, pk)
        conn.close()
        return [(row[1], row[2]) for row in info]

    def show_all(self, table: str, limit: int = 20):
        if table not in SCHEMA_COLUMNS:
            raise QueryError(f"Unknown table '{table}'.")
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table} LIMIT ?", (limit,))
        rows = cur.fetchall()
        columns = SCHEMA_COLUMNS[table]
        conn.close()
        return columns, rows

    def count(self, table: str, column: str = None, value=None):
        if table not in SCHEMA_COLUMNS:
            raise QueryError(f"Unknown table '{table}'.")
        conn = self._connect()
        cur = conn.cursor()
        if column and value and column in SCHEMA_COLUMNS[table]:
            query = f"SELECT COUNT(*) FROM {table} WHERE {column} LIKE ?"
            cur.execute(query, (f"%{value}%",))
        else:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
        result = cur.fetchone()[0]
        conn.close()
        return result

    def filter_rows(self, table: str, column: str, operator: str, value, limit: int = 20):
        if table not in SCHEMA_COLUMNS:
            raise QueryError(f"Unknown table '{table}'.")

        if column is None:
            raise QueryError(
                f"I couldn't tell which field to filter on for '{table}'. "
                "Try being more specific, e.g. 'salary over 90000'."
            )
        if column not in SCHEMA_COLUMNS[table]:
            column = DEFAULT_FILTER_COLUMN.get(table, "id")

        if operator not in (">", "<", "=", "LIKE"):
            raise QueryError(f"Unsupported operator '{operator}'.")

        conn = self._connect()
        cur = conn.cursor()

        if operator == "LIKE":
            query = f"SELECT * FROM {table} WHERE {column} LIKE ? LIMIT ?"
            cur.execute(query, (f"%{value}%", limit))
        else:
            query = f"SELECT * FROM {table} WHERE {column} {operator} ? LIMIT ?"
            cur.execute(query, (value, limit))

        rows = cur.fetchall()
        columns = SCHEMA_COLUMNS[table]
        conn.close()
        return columns, rows
