"""
"""

# =========================================================================== #
from remir.writers import SQLite3Interface, sqlite_adapt
from src.python.extractors import *

# =========================================================================== #
DB_PATH = "data/data.db"

sql = SQLite3Interface("data/data.db")

extractors = [
    EssentiaRelativeMode(),
    LibrosaRelativeMode(),
    LibrosaOnsets(),
    EssentiaOnsets(),
    MIRtoolboxOnsets(),
    MIRtoolboxRelativeMode()
]

for e in extractors:
    sql.insert(
        "extractors",
        sqlite_adapt(e.to_record())
    )

# =========================================================================== #
