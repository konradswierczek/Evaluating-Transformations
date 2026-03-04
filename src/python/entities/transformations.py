"""
"""

from dataclasses import dataclass,asdict
from pathlib import Path
from typing import Literal, Optional
from src.python.entities.files import RealFile
import json

@dataclass(frozen=True)
class Soundfont(RealFile):
    def __post_init__(self):
        super().__post_init__()

        if self.path.suffix.lower() != ".sf2":
            raise ValueError(f"{self.path} is not a .sf2 soundfont.")

@dataclass(frozen=True)
class Midi(RealFile):
    def __post_init__(self):
        super().__post_init__()

        if self.path.suffix.lower() != ".mid":
            raise ValueError(f"{self.path} is not a .mid file.")

@dataclass(frozen=True)
class Audio(RealFile):
    def __post_init__(self):
        super().__post_init__()

        # Validate

@dataclass(frozen=True)
class ImpulseResponse(RealFile):
    def __post_init__(self):
        super().__post_init__()
        if self.path.suffix.lower() != ".wav":
            raise ValueError(f"{self.path} is not a .wav file")

@dataclass(frozen=True)
class Quality:
    format: Literal["wav", "mp3"]
    sample_rate: int
    bitrate: Optional[int] = None
    vbr_level: Optional[int] = None

    def __post_init__(self):
        if self.format == "wav":
            if self.sample_rate not in {22050, 44100, 48000, 96000}:
                raise ValueError(f"WAV sample_rate {self.sample_rate} not supported")
            if self.bitrate is not None or self.vbr_level is not None:
                raise ValueError("WAV does not use bitrate or vbr_level")

        elif self.format == "mp3":
            cbr_allowed = {
                22050: {64, 96, 128, 160},
                44100: {64, 96, 128, 160, 192, 256, 320},
            }

            vbr_allowed = {0, 2, 4, 6}

            if self.vbr_level is not None:
                if self.bitrate is not None:
                    raise ValueError("MP3 VBR should not have a fixed bitrate")
                if self.vbr_level not in vbr_allowed:
                    raise ValueError(f"Invalid MP3 VBR level {self.vbr_level}")
                if self.sample_rate not in cbr_allowed:
                    raise ValueError(f"MP3 sample_rate {self.sample_rate} not allowed for VBR")
            else:
                if self.bitrate not in cbr_allowed.get(self.sample_rate, set()):
                    raise ValueError(
                        f"Invalid MP3 CBR bitrate {self.bitrate} for {self.sample_rate} Hz"
                    )
        else:
            raise ValueError(f"Unsupported format: {self.format}")

    def label(self) -> str:
        if self.format == "wav":
            return f"WAV {self.sample_rate/1000:.1f}kHz"
        if self.vbr_level is not None:
            return f"MP3 V0 @ {self.sample_rate/1000:.1f}kHz"
        return f"MP3 {self.bitrate}kbps @ {self.sample_rate/1000:.1f}kHz"

@dataclass(frozen=True)
class TransformationVector:
    articulation: float = 1
    tempo_ratio: float = 1
    velocity: float = 64
    transposition: int = 0
    soundfont: Optional[Soundfont] = None
    impulse_response: Optional[ImpulseResponse] = None
    reverb_level: int = 0
    loudness: Optional[float] = None
    quality: Optional[Quality] = None

    def __post_init__(self):
        if not 0 < self.articulation <= 1:
            raise ValueError("articulation must be numeric greater than 0 and less than or equal to 1.")

        if not 0 < self.tempo_ratio:
            raise ValueError("tempo_ratio must be numeric greater than 0.")

        if not (isinstance(self.velocity, int) and 0 < self.velocity < 128):
            raise ValueError("velocity must be an integer greater than 0 and less than 128.")

        if not (isinstance(self.transposition, int) and -128 < self.transposition < 128):
            raise ValueError("transposition must be integer greater than -128 and less than 128.")

        if self.loudness is not None:
            if not -60 < self.loudness < -1:
                raise ValueError("loudness must be between -60 and -1 dB, or None to skip")

        if self.soundfont is not None and not isinstance(self.soundfont, Soundfont):
            raise TypeError("soundfont must be a Soundfont instance")

        if self.impulse_response is not None and not isinstance(self.impulse_response, ImpulseResponse):
            raise TypeError("impulse_response must be an ImpulseResponse instance")

        if self.impulse_response is not None:
            if self.reverb_level is None or self.reverb_level <= 0:
                raise ValueError("reverb_level must be > 0 when using impulse_response")

        if self.quality is not None and not isinstance(self.quality, Quality):
            raise TypeError("quality must be an Quality instance")

    def __hash__(self):
        # Convert object fields to hashable representations
        soundfont_hash = hash(self.soundfont.path) if self.soundfont else None
        ir_hash = hash(self.impulse_response.path) if self.impulse_response else None
        quality_hash = hash((
            self.quality.format,
            self.quality.sample_rate,
            self.quality.bitrate,
            self.quality.vbr_level
        )) if self.quality else None

        return hash((
            self.articulation,
            self.tempo_ratio,
            self.velocity,
            self.transposition,
            soundfont_hash,
            ir_hash,
            self.loudness,
            quality_hash
        ))

    def __eq__(self, other):
        if not isinstance(other, TransformationVector):
            return False

        return (
            self.articulation == other.articulation and
            self.tempo_ratio == other.tempo_ratio and
            self.velocity == other.velocity and
            self.transposition == other.transposition and
            (self.soundfont.path if self.soundfont else None) ==
            (other.soundfont.path if other.soundfont else None) and
            (self.impulse_response.path if self.impulse_response else None) ==
            (other.impulse_response.path if other.impulse_response else None) and
            self.loudness == other.loudness and
            (
                (self.quality.format, self.quality.sample_rate, self.quality.bitrate, self.quality.vbr_level)
                if self.quality else None
            ) ==
            (
                (other.quality.format, other.quality.sample_rate, other.quality.bitrate, other.quality.vbr_level)
                if other.quality else None
            )
        )

    def to_record(self) -> dict:
        """
        Convert the TransformationVector into a dictionary suitable for SQLite storage.
        Nested objects are converted to JSON-friendly representations.
        """
        record = {
            "uid": f"{self.__hash__():x}",  # hex representation of hash as unique id
            "articulation": self.articulation,
            "tempo_ratio": self.tempo_ratio,
            "velocity": self.velocity,
            "transposition": self.transposition,
            "reverb_level": self.reverb_level,
            "loudness": self.loudness,
            # Nested objects
            "soundfont": json.dumps(
                {"path": self.soundfont.path, "name": getattr(self.soundfont, "name", None)}
            ) if self.soundfont else None,
            "impulse_response": json.dumps(
                {"path": self.impulse_response.path, "name": getattr(self.impulse_response, "name", None)}
            ) if self.impulse_response else None,
            "quality": json.dumps(
                {
                    "format": self.quality.format,
                    "sample_rate": self.quality.sample_rate,
                    "bitrate": self.quality.bitrate,
                    "vbr_level": getattr(self.quality, "vbr_level", None)
                }
            ) if self.quality else None,
        }
        return record

    def signature(self) -> str:
        def fmt_float(x, precision):
            if x is None:
                return "none"
            return f"{x:.{precision}f}".replace(".", "p")

        def fmt_int(x, width=None):
            if x is None:
                return "none"
            return f"{x:0{width}d}" if width else f"{x}"

        parts = [
            f"tr{fmt_int(self.transposition)}",
            f"vel{fmt_int(self.velocity, 3)}",
            f"tempo{fmt_float(self.tempo_ratio, 2)}",
            f"art{fmt_float(self.articulation, 2)}",
            f"loud{fmt_float(self.loudness, 1)}",
            f"rev{fmt_int(self.reverb_level, 2)}",
        ]

        if self.soundfont is None:
            parts.append("sfnone")
        else:
            parts.append(f"sf{self.soundfont.name}")

        if self.impulse_response is None:
            parts.append("irnone")
        else:
            parts.append(f"ir{self.impulse_response.name}")

        return "_".join(parts)
