"""
"""

# =========================================================================== #
# Built-in Imports.
from pathlib import Path
import logging

# Third Party Imports.
from tqdm import tqdm

# Local Imports.
from src.python.extractors import *
from src.python.entities.files import AudioFileID
from src.python.sql import SQLiteInterface, sqlite_adapt
from src.python.timer import Timer
from src.python.logger import get_logger, log_exception

# =========================================================================== #
# Setup.
DB_PATH = "data/data.db"
sql = SQLiteInterface(DB_PATH)

ti = Timer(
    sql=sql,
    store_events=False
)

logger = get_logger(
    sql,
    console_level=logging.INFO,
    db_level=logging.INFO
)
logger.info("Started Analyzing Files...")

with ti.track(
    "setup",
    category="setup"
):
    audio_path = Path("etc/audio")
    # TODO: In future, maybe don't load list of all files in memory... Could become a problem for large analyses.
    audio_files = [p for p in audio_path.rglob("*") if p.is_file()]

    # Establish extractors.
    extractors = [
        EssentiaRelativeMode(),
        LibrosaRelativeMode(),
        LibrosaOnsets(),
        EssentiaOnsets()
    ]

    # Setup progress bar.
    pb = tqdm(
        total = len(audio_files),
        desc = "Files Analyzed: "
    )

# =========================================================================== #
# Analsis Loop.
for a_idx, audio_file in enumerate(audio_files):
    audio_id = AudioFileID(audio_file)
    # TODO: Could do FKs, let db enforce.
    existing = sql.execute_raw(
        "SELECT * FROM files WHERE uid = ?;",
        (audio_id.sha256, )
    )
    if not existing:
        log_exception(
            logger,
            f"File not found in DB, skipping: {audio_file}",
            file=audio_id.sha256
        )
        continue

    for e_idx, e in enumerate(extractors):
        try:
            with ti.track(
                "extract_feature",
                category="features",
                iteration = e_idx,
                meta = {
                    "extractor": e.uid,
                    "file": audio_id.sha256
                }
            ):
                f = e.extract(str(audio_file))

            with ti.track(
                "write_feature",
                category="data",
                iteration = e_idx,
                meta = {
                    "extractor": e.uid,
                    "file": audio_id.sha256
                }
            ):
                sql.write(
                    "features",
                    sqlite_adapt({
                        "file_uid": audio_id.sha256,
                        "extractor_uid": e.uid,
                        "value": f
                    })
                )
        except Exception as exc:
            log_exception(
                logger,
                "Feature extraction failed",
                extractor=e.uid,
                file=audio_id.sha256
            )

    pb.update(1)

logger.info("Finished Analyzing Files...")
pb.close()
