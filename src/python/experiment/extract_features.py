"""
"""

# =========================================================================== #
# Built-in Imports.
from pathlib import Path
import logging

# Third Party Imports.
from tqdm import tqdm
from remir.entities import AudioFileID
from remir.writers import SQLite3Interface, sqlite_adapt
from remir.timer import Timer
from remir.logger import get_logger, log_exception

# Local Imports.
from src.python.extractors import *

# =========================================================================== #
# Setup.
DB_PATH = "data/data.db"
sql = SQLite3Interface(DB_PATH)

ti = Timer(
    writer=lambda record: sql.insert("timing", record),
    store_events=False
)

logger = get_logger(
    writer=lambda r: sql.insert("logs", r),
    console_level=logging.INFO,
    writer_level=logging.INFO
)
logger.info("Started Analyzing Files...")

with ti.track(
    "extraction_setup",
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
    # TODO: Check if file exists in DB.
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
                sql.insert(
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
