"""

"""
# TODO: Remove duplicate files

# =========================================================================== #
# Built-in Imports.
from pathlib import Path
import logging
from datetime import datetime, timezone

# Third Party Imports.
from tqdm import tqdm

# Local Imports.
from pyramidi import (
    PyraMIDIFile,
    MIDI2Audio,
    SetVelocity,
    TransformTempo,
    TransformPitch,
    SynthesizeAudio,
    changes_from_spec
)
from remir.entities import AudioFileID, MIDIFileID
from remir.writers import SQLite3Interface, sqlite_adapt
from remir.timer import Timer
from remir.logger import get_logger, log_exception
from remir.system import get_all_system_data

from src.python.file_namer import filename_from_spec

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
logger.info("Started Generating Files...")

# TODO: Add timer?
# Generate timestamp-based UID (UTC, microseconds).
run_uid = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
# Collect system + git metadata.
run_metadata = get_all_system_data()
# Write system metadata.
sql.insert(
    "runs",
    sqlite_adapt({
        "uid": run_uid,
        "type": "generate",
        "metadata": run_metadata
    })
)

logger.info("Started Generating Files...")

with ti.track(
    "generation_setup",
    category="setup"
):
    # Establish the transformations.
    transposition_range = range(-7, 8)
    velocity_range = range(24, 105, 2)
    tempo_range = [0.75 + i * 0.01 for i in range(51)]
    change_vectors = [
        [TransformPitch(t), SynthesizeAudio()] for t in range(-7, 8)
    ] + [
        [SetVelocity(v), SynthesizeAudio()] for v in range(24, 105, 2)
    ] + [
        [TransformTempo(tempo), SynthesizeAudio()] for tempo in [0.75 + i * 0.01 for i in range(51)]
    ]

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
    midi = PyraMIDIFile(midi_file)
    piece_folder = audio_path / midi_file.stem
    piece_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    for t_idx, t in enumerate(change_vectors):
        try:
            changer = MIDI2Audio(t)
            audio_file_name = filename_from_spec(changer)
            output_path = piece_folder / f"{audio_file_name}.wav"

            with ti.track(
                "generate_audio_file",
                category="generation",
                iteration=t_idx,
                meta={
                    "seed_file": str(midi_file),
                    "change_vector": changer.to_spec()
                }
            ):

                audio_file = AudioFileID(
                    changer.apply(midi, output_path),
                    extra={
                        "change_vector": changer.to_spec(),
                        "midi_file": midi_id.to_record()
                    }
                )

            with ti.track(
                "write_file",
                category="data",
                iteration=m_idx,
                meta={
                    "seed_file": str(midi_file),
                    "change_vector": changer.to_spec()
                }
            ):
                sql.insert(
                    "files",
                    sqlite_adapt(audio_file.to_record())
                )

        except Exception as exc:
            log_exception(
                logger,
                "File generation failed",
                file=str(midi_file),
                change_vector = changer.to_spec()
            )
            continue

    pb.update(1)

logger.info("Finished Generating Files...")
pb.close()
