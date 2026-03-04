"""
Generic SQLite3 Interface
Supports writing dictionaries to tables, with a clean foundation for future read/query operations.
"""

import sqlite3
import logging
from typing import Any
import json

logger = logging.getLogger(__name__)


class SQLiteInterface:
    """
    A generic, extensible interface for interacting with a SQLite3 database.

    Usage:
        db = SQLiteInterface("my_database.db")
        db.write("users", {"name": "Alice", "age": 30})
        db.write_many("users", [{"name": "Bob", "age": 25}, {"name": "Carol", "age": 35}])
        db.close()

    Or as a context manager:
        with SQLiteInterface("my_database.db") as db:
            db.write("users", {"name": "Alice", "age": 30})
    """

    def __init__(self, db_path: str, auto_create_tables: bool = True):
        """
        Initialize the interface and open a connection.

        Args:
            db_path: Path to the SQLite database file. Use ":memory:" for an in-memory DB.
            auto_create_tables: If True, tables are automatically created from dict keys on first write.
        """
        self.db_path = db_path
        self.auto_create_tables = auto_create_tables
        self._connection: sqlite3.Connection | None = None
        self._connect()

    # -------------------------------------------------------------------------
    # Connection management
    # -------------------------------------------------------------------------

    def _connect(self) -> None:
        self._connection = sqlite3.connect(self.db_path)
        self._connection.row_factory = sqlite3.Row  # rows behave like dicts
        logger.debug("Connected to SQLite database: %s", self.db_path)

    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.debug("Connection closed.")

    def __enter__(self) -> "SQLiteInterface":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            self._connection.commit()
        else:
            self._connection.rollback()
        self.close()

    @property
    def connection(self) -> sqlite3.Connection:
        if self._connection is None:
            raise RuntimeError("Database connection is not open.")
        return self._connection

    # -------------------------------------------------------------------------
    # Schema helpers
    # -------------------------------------------------------------------------

    def _infer_sql_type(self, value: Any) -> str:
        """Map a Python value to a SQLite column type."""
        if isinstance(value, bool):
            return "INTEGER"
        if isinstance(value, int):
            return "INTEGER"
        if isinstance(value, float):
            return "REAL"
        if isinstance(value, bytes):
            return "BLOB"
        return "TEXT"

    def create_table(self, table: str, schema: dict[str, str], if_not_exists: bool = True) -> None:
        """
        Explicitly create a table from a {column: sql_type} schema dict.

        Args:
            table: Table name.
            schema: Mapping of column name -> SQLite type (e.g. {"name": "TEXT", "age": "INTEGER"}).
            if_not_exists: Use IF NOT EXISTS clause.
        """
        qualifier = "IF NOT EXISTS" if if_not_exists else ""
        columns = ", ".join(f'"{col}" {typ}' for col, typ in schema.items())
        sql = f'CREATE TABLE {qualifier} "{table}" (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns});'
        self.connection.execute(sql)
        self.connection.commit()
        logger.debug("Table '%s' ensured.", table)

    def _auto_create_table(self, table: str, row: dict) -> None:
        """Create a table inferred from the keys/values of a sample dict."""
        schema = {col: self._infer_sql_type(val) for col, val in row.items()}
        self.create_table(table, schema)

    def _ensure_columns(self, table: str, row: dict) -> None:
        """Add any missing columns to an existing table (ALTER TABLE ADD COLUMN)."""
        existing = {info[1] for info in self.connection.execute(f'PRAGMA table_info("{table}")').fetchall()}
        for col, val in row.items():
            if col not in existing:
                sql_type = self._infer_sql_type(val)
                self.connection.execute(f'ALTER TABLE "{table}" ADD COLUMN "{col}" {sql_type};')
                logger.debug("Added column '%s' (%s) to table '%s'.", col, sql_type, table)
        self.connection.commit()

    def _table_exists(self, table: str) -> bool:
        result = self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table,)
        ).fetchone()
        return result is not None

    # -------------------------------------------------------------------------
    # Write operations
    # -------------------------------------------------------------------------

    def write(self, table: str, row: dict, commit: bool = True) -> int:
        """
        Insert a single dictionary as a row into the specified table.

        Args:
            table: Target table name.
            row: Dictionary of {column: value} pairs.
            commit: Commit immediately after insert.

        Returns:
            The rowid (lastrowid) of the inserted row.
        """
        if not row:
            raise ValueError("Cannot write an empty dictionary.")

        if self.auto_create_tables:
            if not self._table_exists(table):
                self._auto_create_table(table, row)
            else:
                self._ensure_columns(table, row)

        columns = ", ".join(f'"{col}"' for col in row)
        placeholders = ", ".join("?" for _ in row)
        sql = f'INSERT INTO "{table}" ({columns}) VALUES ({placeholders});'

        cursor = self.connection.execute(sql, list(row.values()))
        if commit:
            self.connection.commit()
        logger.debug("Inserted row into '%s' with id %d.", table, cursor.lastrowid)
        return cursor.lastrowid

    def write_many(self, table: str, rows: list[dict], commit: bool = True) -> int:
        """
        Insert multiple dictionaries into the specified table efficiently.
        All rows must share the same keys.

        Args:
            table: Target table name.
            rows: List of dicts with identical keys.
            commit: Commit after all inserts.

        Returns:
            Number of rows inserted.
        """
        if not rows:
            return 0

        # Validate uniform keys
        keys = list(rows[0].keys())
        if not all(list(r.keys()) == keys for r in rows):
            raise ValueError("All rows in write_many must have the same keys.")

        if self.auto_create_tables:
            if not self._table_exists(table):
                self._auto_create_table(table, rows[0])
            else:
                self._ensure_columns(table, rows[0])

        columns = ", ".join(f'"{col}"' for col in keys)
        placeholders = ", ".join("?" for _ in keys)
        sql = f'INSERT INTO "{table}" ({columns}) VALUES ({placeholders});'

        values = [list(row.values()) for row in rows]
        self.connection.executemany(sql, values)
        if commit:
            self.connection.commit()
        logger.debug("Inserted %d rows into '%s'.", len(rows), table)
        return len(rows)

    # -------------------------------------------------------------------------
    # Placeholder stubs for future operations
    # -------------------------------------------------------------------------

    def read(self, table: str, filters: dict | None = None) -> list[dict]:
        """
        [Stub] Read rows from a table, optionally filtered by column values.
        To be implemented.
        """
        raise NotImplementedError("read() is not yet implemented.")

    def update(self, table: str, updates: dict, filters: dict) -> int:
        """
        [Stub] Update rows matching filters with the given values.
        To be implemented.
        """
        raise NotImplementedError("update() is not yet implemented.")

    def delete(self, table: str, filters: dict) -> int:
        """
        [Stub] Delete rows matching filters.
        To be implemented.
        """
        raise NotImplementedError("delete() is not yet implemented.")

    def execute_raw(self, sql: str, params: tuple = ()) -> list[dict]:
        """
        Execute a raw SQL statement and return results as a list of dicts.
        Useful for complex queries until higher-level methods are implemented.
        """
        cursor = self.connection.execute(sql, params)
        self.connection.commit()
        return [dict(row) for row in cursor.fetchall()]

    def apply_schema(self, schema_path: str, ignore_existing: bool = True) -> None:
        """Read and execute a .sql schema file against the database."""
        with open(schema_path, "r") as f:
            sql = f.read()
        self.connection.executescript(sql)
        logger.debug("Schema applied from %s", schema_path)

    def table_exists(self, table: str) -> bool:
        """Return True if the table exists in the database."""
        return self._table_exists(table)
# -----------------------------------------------------------------------------
# Quick demo
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    with SQLiteInterface(":memory:") as db:
        # Single write
        db.write("products", {"name": "Widget", "price": 9.99, "stock": 100})
        db.write("products", {"name": "Gadget", "price": 24.99, "stock": 50})

        # Batch write
        db.write_many("users", [
            {"username": "alice", "email": "alice@example.com", "age": 30},
            {"username": "bob",   "email": "bob@example.com",   "age": 25},
        ])

        # Raw query (until read() is implemented)
        products = db.execute_raw("SELECT * FROM products;")
        print("Products:", products)

        users = db.execute_raw("SELECT * FROM users;")
        print("Users:", users)

def sqlite_adapt(record: dict[str, Any]) -> dict[str, Any]:
    """
    Convert a dictionary into a SQLite-safe dictionary.

    - dict/list/tuple/set → JSON string
    - bool → int
    - None/int/float/str/bytes → unchanged
    """

    def adapt_value(value: Any) -> Any:
        if value is None:
            return None

        if isinstance(value, bool):
            return int(value)

        if isinstance(value, (dict, list, tuple, set)):
            return json.dumps(value, sort_keys=True)

        return value

    return {k: adapt_value(v) for k, v in record.items()}

