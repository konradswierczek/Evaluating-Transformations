"""
"""

# =========================================================================== #
import logging

from src.python.sql import SQLiteInterface, sqlite_adapt
from src.python.extractors import *

# =========================================================================== #
DB_PATH = "data/data.db"

sql = SQLiteInterface("data/data.db")
sql.apply_schema("schema.sql")

extractors = [
    EssentiaRelativeMode(),
    LibrosaRelativeMode(),
    LibrosaOnsets(),
    EssentiaOnsets(),
    MIRtoolboxOnsets(),
    MIRtoolboxRelativeMode()
]

for e in extractors:
    sql.write(
        "extractors",
        sqlite_adapt(e.to_record())
    )

# =========================================================================== #
