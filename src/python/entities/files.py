"""
"""

# ================================================================================================ #
# Built-in Imports.
from pathlib import Path
import os
from hashlib import sha256
from dataclasses import dataclass, field
from typing import Dict, Optional
# Third-party Imports.
from soundfile import info
from mido import MidiFile


__all__ = ["RealFile", "IdentifiedFile", "AudioFileID", ]

# ================================================================================================ #
@dataclass(frozen=True)
class RealFile:
    """Verify that a file exists in the current file system.

    Parameters:
    path (str | os.pathLike) -- A filepath.
 
    """
    path: str | os.PathLike
    extra: Optional[Dict] = None

    def __post_init__(self):
        p = Path(self.path)

        if not p.exists():
            raise FileNotFoundError(p)

        if not p.is_file():
            raise ValueError(f"{p} is not a file")

        object.__setattr__(self, "path", p.resolve())

    def __fspath__(self):
        return str(self.path)

# ================================================================================================ #
@dataclass(frozen=True)
class IdentifiedFile(RealFile):
    """Identify a file based on its contents.

    Parameters:
    sha256 (str) -- Hash of the file contents based on sha256.
    filename (str) -- The normalized filename of the input file.
    file_size (int) -- File size in bytes.
    """

    sha256: str = field(init=False)
    filename: str = field(init=False)
    file_size: int = field(init=False)

    def __post_init__(self):
        super().__post_init__()

        object.__setattr__(self, "filename", self.path.name)
        object.__setattr__(self, "file_size", self.path.stat().st_size)
        object.__setattr__(self, "sha256", self._compute_sha256())

    def _compute_sha256(self, chunk_size: int = 8192) -> str:
        hasher = sha256()
        with self.path.open("rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def same_bytes(self, other: "IdentifiedFile") -> bool:
        """Check if two file have the same hash identities."""
        return self.sha256 == other.sha256

# ================================================================================================ #
@dataclass(frozen=True)
class AudioFileID(IdentifiedFile):
    """Identify an audio file on the basis of its container data."""

    container: Dict[str, object] = field(init=False)

    def __post_init__(self):
        super().__post_init__()
        object.__setattr__(self, "container", self._compute_container_signature())

    def _compute_container_signature(self) -> Dict[str, object]:
        audio_info = info(self.path)
        return {
            "samplerate": audio_info.samplerate,
            "channels": audio_info.channels,
            "frames": audio_info.frames,
            "duration": audio_info.frames / audio_info.samplerate,
            "format": audio_info.format,
            "subtype": audio_info.subtype,
        }

    def same_container(self, other: "AudioFileIdentity") -> bool:
        return self.container == other.container

    def to_record(self):
        return {
            "uid": self.sha256,
            "file_name": self.filename,
            "file_size": self.file_size,
            **self.container,
            "extra": self.extra,
        }

# ================================================================================================ #
@dataclass(frozen=True)
class MIDIFileID(IdentifiedFile):
    """Identify a MIDI file based on its container data."""

    container: Dict[str, object] = field(init=False)

    def __post_init__(self):
        super().__post_init__()
        object.__setattr__(self, "container", self._compute_container_signature())

    def _compute_container_signature(self) -> Dict[str, object]:
        mid = MidiFile(self.path)

        return {
            "type": mid.type,
            "ticks_per_beat": mid.ticks_per_beat,
            "tracks": len(mid.tracks),
            "length_seconds": mid.length,
        }

    def same_container(self, other: "MIDIFileID") -> bool:
        return self.container == other.container

    def to_record(self):
        return {
            "uid": self.sha256,
            "file_name": self.filename,
            "file_size": self.file_size,
            **self.container,
            "extra": self.extra,
        }

# ================================================================================================ #
