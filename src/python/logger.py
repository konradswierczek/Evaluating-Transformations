# sql_logger.py
"""
SQLite-backed logger: tqdm-safe console + live DB logging + exception capture.
"""
import logging
from typing import Any, Optional

from tqdm import tqdm

from src.python.sql import SQLiteInterface, sqlite_adapt


# -------------------------------------------------------------------------
# Handlers
# -------------------------------------------------------------------------

class TqdmHandler(logging.StreamHandler):
    """Console handler safe with tqdm progress bars."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)


class SQLiteHandler(logging.Handler):

    def __init__(self, sql: SQLiteInterface, table: str = "logs"):
        super().__init__()
        self.sql = sql
        self.table = table
        self.sql.create_table(table, {
            "time":      "TEXT",
            "level":     "TEXT",
            "name":      "TEXT",
            "message":   "TEXT",
            "exception": "TEXT",
            "context":   "TEXT",
        })
        self._time_formatter = logging.Formatter(datefmt="%Y-%m-%d %H:%M:%S")

    def emit(self, record: logging.LogRecord) -> None:
        try:
            exc_str = (
                self._time_formatter.formatException(record.exc_info)
                if record.exc_info else None
            )

            row = sqlite_adapt({
                "time":      self._time_formatter.formatTime(record),
                "level":     record.levelname,
                "name":      record.name,
                "message":   record.getMessage(),
                "exception": exc_str,
                "context":   getattr(record, "ctx", None),
            })
            self.sql.write(self.table, row)

        except Exception as e:
            tqdm.write(f"[LOGGING ERROR] Could not write to SQLite: {e}")
            tqdm.write(record.getMessage())


# -------------------------------------------------------------------------
# Exception logging helper
# -------------------------------------------------------------------------

def log_exception(
    logger: logging.Logger,
    message: str,
    level: int = logging.ERROR,
    **context: Any,
) -> None:
    """
    Log an exception with arbitrary key/value context stored in the
    `context` column of the SQLite log table.

    Must be called from inside an except block (uses current exc_info).

    Usage:
        try:
            process(filepath)
        except Exception:
            log_exception(logger, "File processing failed",
                          filepath=str(path), stage="extraction")

    Args:
        logger:   Your logger instance.
        message:  Human-readable description of what failed.
        level:    Log level (default ERROR).
        **context: Arbitrary key/value pairs stored in the `context` column.
    """
    logger.log(
        level,
        message,
        exc_info=True,
        extra={"ctx": context} if context else {},
        stacklevel=2,
    )


# -------------------------------------------------------------------------
# Logger factory
# -------------------------------------------------------------------------

def get_logger(
    sql: SQLiteInterface,
    name: Optional[str] = None,
    console_level: int = logging.INFO,
    db_level: int = logging.DEBUG,
    table: str = "logs",
    datefmt: str = "%Y-%m-%d %H:%M:%S",
) -> logging.Logger:
    """
    Returns a logger that writes to a tqdm-safe console and a SQLite DB.

    The DB captures everything at `db_level` and above, including full
    exception tracebacks and any structured context passed via log_exception().

    Args:
        sql:           An open SQLiteInterface instance.
        name:          Logger name (default: root logger).
        console_level: Minimum level for console output.
        db_level:      Minimum level for DB output.
        table:         Table name to write log rows into.
        datefmt:       Datetime format string for console output.
    """
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.setLevel(min(console_level, db_level))

    ch = TqdmHandler()
    ch.setLevel(console_level)
    ch.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", datefmt=datefmt
    ))
    logger.addHandler(ch)

    sh = SQLiteHandler(sql, table)
    sh.setLevel(db_level)
    logger.addHandler(sh)

    return logger