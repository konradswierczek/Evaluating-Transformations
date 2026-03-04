"""
"""


from os import remove
import tempfile
from pathlib import Path
from typing import Optional
# Third-party Imports
from mido import MidiFile
# Local/Owned Imports
from pyramidi.transform import *
from pyramidi.synthesize import *
from pyramidi.parse import collapse_tracks
from src.python.entities.transformations import TransformationVector


def generate_audio(
    transformations: TransformationVector,
    seed_midi: Path,
    output_file: Optional[Path] = None
):
    midi = MidiFile(seed_midi)
    midi = collapse_tracks(midi)

    # --------------------------
    # Transform MIDI
    # --------------------------
    transform_pipeline = TransformMidi(midi)
    transform_pipeline.add(change_articulation, articulation=transformations.articulation)
    transform_pipeline.add(change_tempi_ratio, ratio=transformations.tempo_ratio)
    transform_pipeline.add(change_velocity, velocity=transformations.velocity)
    transform_pipeline.add(change_transposition, semitones=transformations.transposition)
    new_midi = transform_pipeline.render()

    temp_midi_path = Path(tempfile.mktemp(suffix=".mid"))
    new_midi.save(temp_midi_path)

    render_pipeline = RenderAudio(temp_midi_path)

    # Always synthesize, default soundfont if none provided
    soundfont_path = transformations.soundfont.path if transformations.soundfont else ""
    render_pipeline.add(render_audio, soundfont=soundfont_path)

    if transformations.impulse_response is not None:
        render_pipeline.add(
            render_reverb,
            ir_file=transformations.impulse_response.path,
            dry=1,
            wet=transformations.reverb_level
        )

    if transformations.loudness is not None:
        render_pipeline.add(render_loudness_ebur128, target_lufs=transformations.loudness)

    # --------------------------
    # Handle Quality
    # --------------------------
    if transformations.quality:
        quality = transformations.quality

        # Determine output extension
        if output_file is None:
            ext = ".wav" if quality.format == "wav" else ".mp3"
            output_file = Path(tempfile.mktemp(suffix=ext))

        if quality.format == "wav":
            pass  # WAV: nothing to do
        elif quality.format == "mp3":
            if quality.vbr_level is not None:
                render_pipeline.add(
                    render_compression,
                    vbr_quality=quality.vbr_level,
                    sr=quality.sample_rate
                )
            else:
                render_pipeline.add(
                    render_compression,
                    cbr_bitrate=quality.bitrate,  # <-- use cbr_bitrate
                    sr=quality.sample_rate
                )

    # --------------------------
    # Default output file if not set
    # --------------------------
    if output_file is None:
        output_file = Path(tempfile.mktemp(suffix=".wav"))

    new_audio = render_pipeline.run(str(output_file), silent=True)

    # Clean up temporary MIDI
    remove(temp_midi_path)

    return new_audio
