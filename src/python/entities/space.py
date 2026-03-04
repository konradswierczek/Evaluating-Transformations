# This module should define the space we can use for our various params.
from enum import Enum, auto
from typing import Optional

# TODO: Should we check that the range is acceptable by the validatgion class?

class ParameterKind(Enum):
    CONTINUOUS = auto()
    INTEGER = auto()
    CATEGORICAL = auto()

from dataclasses import dataclass
from typing import Any, Sequence

@dataclass(frozen=True)
class ParameterSpec:
    name: str
    kind: ParameterKind
    domain: Any

class Domain:
    def validate(self, value) -> bool:
        raise NotImplementedError

@dataclass(frozen=True)
class FloatDomain(Domain):
    low: float
    high: float
    precision: int | None = None

@dataclass(frozen=True)
class IntDomain(Domain):
    low: int
    high: int

@dataclass(frozen=True)
class ChoiceDomain(Domain):
    values: tuple

def label_of(v) -> str:
    if hasattr(v, "label"):
        return v.label()
    return str(v)
