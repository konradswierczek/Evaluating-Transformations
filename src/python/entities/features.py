from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, Optional
import hashlib
import json
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

#__all__ = [""]

# ----------------------------
# Utilities
# ----------------------------

def get_package_version(pkg: str) -> str:
    try:
        return version(pkg)
    except PackageNotFoundError:
        return "unknown"


def stable_hash(payload: dict[str, Any]) -> str:
    dumped = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


# ----------------------------
# Input domain
# ----------------------------

class InputDomain(str, Enum):
    AUDIO = "audio"
    MIDI = "midi"
    SCORE = "score"


# ----------------------------
# Semantic feature
# ----------------------------

@dataclass(frozen=True)
class Feature:
    name: str
    description: str


# ----------------------------
# Algorithm metadata
# ----------------------------

@dataclass(frozen=True)
class AlgorithmMeta:
    name: str
    tool: str
    version: str
    description: str


# ----------------------------
# Feature output contract
# ----------------------------

@dataclass(frozen=True)
class FeatureOutput:
    dtype: type
    shape: Optional[tuple[Optional[int], ...]]
    description: str


# ----------------------------
# Base FeatureExtractor
# ----------------------------

class FeatureExtractor(ABC):

    FEATURE: ClassVar[Feature]
    ALGO: ClassVar[AlgorithmMeta]
    INPUT_DOMAIN: ClassVar[InputDomain]
    REQUIRED_PACKAGES: ClassVar[tuple[str, ...]] = ()
    DEFAULT_PARAMETERS: ClassVar[dict[str, Any]] = {}

    def __init__(self, **parameters):
        combined = dict(self.DEFAULT_PARAMETERS)
        combined.update(parameters)
        self.parameters = combined

        self.dependencies = {
            pkg: get_package_version(pkg)
            for pkg in self.REQUIRED_PACKAGES
        }

        self.tool_version = get_package_version(
            getattr(self.ALGO, "tool", "unknown")
        )

    # -------- output contract --------

    @property
    @abstractmethod
    def output(self) -> FeatureOutput:
        ...

    def _output_payload(self) -> dict[str, Any]:
        out = self.output
        return {
            "dtype": out.dtype.__name__,
            "shape": out.shape,
            "description": out.description,
        }

    # -------- reproducible UID --------

    @property
    def uid(self) -> str:
        payload = {
            "feature": self.FEATURE.name,
            "algo_name": self.ALGO.name,
            "algo_version": self.ALGO.version,
            "tool": self.ALGO.tool,
            "tool_version": self.tool_version,
            "input_domain": self.INPUT_DOMAIN.value,
            "parameters": dict(sorted(self.parameters.items())),
            "output": self._output_payload(),
        }
        return stable_hash(payload)

    # -------- execution --------

    @abstractmethod
    def extract(self, input_data: Path):
        ...

    # -------- serialization --------

    def to_record(self) -> dict:
        return {
            "uid": self.uid,
            "feature": self.FEATURE.name,
            "feature_description": self.FEATURE.description,
            "extractor": self.ALGO.name,
            "extractor_version": self.ALGO.version,
            "tool": self.ALGO.tool,
            "tool_version": self.tool_version,
            "input_domain": self.INPUT_DOMAIN.value,
            "parameters": dict(sorted(self.parameters.items())),
            "dependencies": self.dependencies,
            "output": self._output_payload(),
        }
