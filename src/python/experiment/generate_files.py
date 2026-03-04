"""

"""

# =========================================================================== #
# Built-in Imports.
from pathlib import Path
import logging
from datetime import datetime, timezone

# Third Party Imports.
from tqdm import tqdm

# Local Imports.
from src.python.generate import generate_audio
from src.python.entities.files import AudioFileID, MIDIFileID
from src.python.entities.transformations import TransformationVector
from src.python.sql import SQLiteInterface, sqlite_adapt
from src.python.timer import Timer
from src.python.logger import get_logger, log_exception
from src.python.system_data import get_all_system_data

# =========================================================================== #
# Setup.
DB_PATH = "data/data.db"
sql = SQLiteInterface(DB_PATH)

# Generate timestamp-based UID (UTC, microseconds).
run_uid = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
# Collect system + git metadata.
run_metadata = get_all_system_data()
# Write system metadata.
sql.write(
    "runs",
    sqlite_adapt({
        "uid": run_uid,
        "type": "generate",
        "metadata": run_metadata
    })
)

ti = Timer(
    sql=sql,
    store_events=False
)

logger = get_logger(
    sql,
    console_level=logging.INFO,
    db_level=logging.INFO
)
logger.info("Started Generating Files...")

with ti.track(
    "setup",
    category="setup"
):
    # Establish the transformations.
    transposition_range = range(-7, 8)
    velocity_range = range(24, 105, 2)
    tempo_range = [0.75 + i * 0.01 for i in range(51)]
    transformation_vectors = [TransformationVector(transposition=t) for t in transposition_range] + \
        [TransformationVector(velocity=v) for v in velocity_range] + \
            [TransformationVector(tempo_ratio=tempo) for tempo in tempo_range]

    # Set paths.
    seed_midi_path = Path("etc/seed_midi")
    audio_path = Path("etc/audio")
    seed_midi_files = [p for p in seed_midi_path.rglob("*") if p.is_file()]
    pb = tqdm(
        total = len(seed_midi_files),
        desc = "Files Generated: "
    )

# =========================================================================== #
# Generation Loop.
for m_idx, midi_file in enumerate(seed_midi_files):
    midi_id = MIDIFileID(midi_file)
    piece_folder = audio_path / midi_file.stem
    piece_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    for t_idx, t in enumerate(transformation_vectors):
        try:
            signature = t.signature()
            output_path = piece_folder / f"{signature}.wav"

            with ti.track(
                "generate_audio_file",
                category="generation",
                iteration=t_idx,
                meta={
                    "seed_file": str(midi_file),
                    "signature": signature
                }
            ):
                audio_file = AudioFileID(
                    generate_audio(
                        t,
                        midi_file,
                        output_path
                    ),
                    extra={
                        "transformation_vector": t.to_record(),
                        "midi_file": midi_id.to_record()
                    }
                )

            with ti.track(
                "write_file",
                category="data",
                iteration=m_idx,
                meta={
                    "seed_file": str(midi_file),
                    "signature": signature
                }
            ):
                sql.write(
                    "files",
                    sqlite_adapt(audio_file.to_record())
                )

        except Exception as exc:
            log_exception(
                logger,
                "File generation failed",
                file=str(midi_file),
                signature=signature
            )
            continue
        
    pb.update(1)

logger.info("Finished Generating Files...")
pb.close()
