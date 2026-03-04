"""
"""

# =========================================================================== #
from pathlib import Path
from typing import Any, Optional

from src.python.entities.features import *

__all__ = [
    "LibrosaOnsets", "LibrosaRelativeMode",
    "EssentiaOnsets", "EssentiaRelativeMode",
    "MIRtoolboxOnsets", "MIRtoolboxRelativeMode"
]

# =========================================================================== #
RELATIVE_MODE = Feature(
    name="relative_mode",
    description="The majorness or minorness of a piece of music."
)

ONSET_DETECTION = Feature(
    name="onset_detection",
    description="The starting times of musical events such as notes or chords."
)

# =========================================================================== #
N_ONSETS_OUTPUT = FeatureOutput(
    dtype=int,
    shape=(),
    description="The number of onsets detected in an audio file."
)

MIRMODE_OUTPUT = FeatureOutput(
    dtype=float,
    shape=(),
    description="Majorness/Minorness. Theoretically ranges between -1 and 1, where lower values are more minor."
)

# =========================================================================== #
class LibrosaOnsets(FeatureExtractor):
    FEATURE = ONSET_DETECTION

    ALGO = AlgorithmMeta(
        name="onset_detect",
        tool="librosa",
        version="1",
        description=(
            "Locate note onset events by picking peaks in a spectral flux "
            "onset strength envelope. The peak_pick parameters were chosen "
            "by large-scale hyper-parameter optimization over the dataset "
            "provided by https://github.com/CPJKU/onset_db."
        ),
    )

    INPUT_DOMAIN = InputDomain.AUDIO
    REQUIRED_PACKAGES = ("librosa", )
    DEFAULT_PARAMETERS = {}

    @property
    def output(self) -> FeatureOutput:
        return N_ONSETS_OUTPUT

    def extract(self, input_file: Path):
        from librosa import load
        from librosa.onset import onset_detect
        y, sr = load(input_file)
        return len(onset_detect(y=y, sr=sr))

# =========================================================================== #
class EssentiaOnsets(FeatureExtractor):
    FEATURE = ONSET_DETECTION

    ALGO = AlgorithmMeta(
        name="onset_detect",
        tool="essentia",
        version="1",
        description=(
            "the Complex-Domain spectral difference function taking into "
            "account changes in magnitude and phase. It emphasizes note "
            "onsets either as a result of significant change in energy in the "
            "magnitude spectrum, and/or a deviation from the expected phase "
            "values in the phase spectrum, caused by a change in pitch."
        ),
    )

    INPUT_DOMAIN = InputDomain.AUDIO
    REQUIRED_PACKAGES = ("essentia", )
    DEFAULT_PARAMETERS = {"method": "complex"}

    @property
    def output(self) -> FeatureOutput:
        return N_ONSETS_OUTPUT

    def extract(self, input_file: Path):
        from essentia.standard import (
            MonoLoader, OnsetDetection, FrameGenerator,
            Windowing, FFT, CartesianToPolar, Onsets
        )
        from essentia import array
        audio = MonoLoader(filename=input_file)()
        od = OnsetDetection(method=self.parameters["method"])
        w, fft, c2p = Windowing(), FFT(), CartesianToPolar()
        od_values = [od(*c2p(fft(w(frame)))) for frame in FrameGenerator(audio)]
        onsets = Onsets()(array([od_values]), [1])
        return len(onsets)

# =========================================================================== #
class LibrosaRelativeMode(FeatureExtractor):
    FEATURE = RELATIVE_MODE

    ALGO = AlgorithmMeta(
        name="relative_mode_cens",
        tool="librosa",
        version="1",
        description=(
            "Compute the chroma variant 'Chroma Energy Normalized' (CENS). "
            "To compute CENS features, following steps are taken after "
            "obtaining chroma vectors using `chroma_cqt()`. L-1 normalization "
            "of each chroma vector, Quantization of amplitude based on "
            "'log-like' amplitude thresholds (optional) Smoothing with "
            "sliding window. Default window length = 41 frames. CENS features "
            "are robust to dynamics, timbre and articulation, thus these are "
            "commonly used in audio matching and retrieval applications. "
            "Copied from https://librosa.org/doc/latest/generated/librosa."
            "feature.chroma_cens.html"
        ),
    )

    INPUT_DOMAIN = InputDomain.AUDIO
    REQUIRED_PACKAGES = ("librosa", "pyramidi", )
    DEFAULT_PARAMETERS = {"keyfinding_weights": "Gomez_MIRtoolbox"}

    @property
    def output(self) -> FeatureOutput:
        return MIRMODE_OUTPUT

    def extract(self, input_file: Path):
        from librosa import load
        from librosa.feature import chroma_cens
        from pyramidi.models.krumhansl90 import keyfinding, mirmode

        y, sr = load(input_file)
        chroma_cens = chroma_cens(y=y, sr=sr)
        chroma_out = {idx: sum(pc) for idx, pc in enumerate(chroma_cens)}
        key_coefis = keyfinding(chroma_out, self.parameters["keyfinding_weights"])
        return mirmode(key_coefis)

# =========================================================================== #
class EssentiaRelativeMode(FeatureExtractor):
    FEATURE = RELATIVE_MODE

    ALGO = AlgorithmMeta(
        name="relative_mode_cqt",
        tool="essentia",
        version="1",
        description=(
            "mirmode using Constant-Q Transform in Essentia. Computes the "
            "Constant-Q chromagram using FFT. It transforms a windowed audio "
            "frame into the log frequency domain. Copied from https://essentia"
            ".upf.edu/reference/std_Chromagram.html. Uses keyfinding from "
            "pyramidi. "
        ),
    )

    INPUT_DOMAIN = InputDomain.AUDIO
    REQUIRED_PACKAGES = ("essentia", "pyramidi", )
    DEFAULT_PARAMETERS = {"keyfinding_weights": "Gomez_MIRtoolbox"}

    @property
    def output(self) -> FeatureOutput:
        return MIRMODE_OUTPUT

    def extract(self, input_file: Path):
        from essentia.standard import (
            MonoLoader, FrameGenerator, Chromagram
        )
        from pyramidi.models.krumhansl90 import keyfinding, mirmode

        audio = MonoLoader(filename=input_file)()
        chromagram_alg = Chromagram()
        chromagram_sum = [0.0] * 12
        for frame in FrameGenerator(audio, frameSize=32768):
            chroma_frame = chromagram_alg(frame)
            chromagram_sum = [a + b for a, b in zip(chromagram_sum, chroma_frame)]
        chromagram = {i: chromagram_sum[(i + 3) % 12] for i in range(12)}
        key_coefis = keyfinding(chromagram, self.parameters["keyfinding_weights"])
        return mirmode(key_coefis)

# =========================================================================== #
class MIRtoolboxBaseExtractor(FeatureExtractor):
    _engine = None
    _path_added = False

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            import matlab.engine
            cls._engine = matlab.engine.start_matlab(
                "-nodisplay -nosplash -nodesktop"
            )

            # Disable all graphics
            cls._engine.eval("set(0,'DefaultFigureVisible','off');", nargout=0)
            cls._engine.eval("warning off;", nargout=0)

        if not cls._path_added:
            mirtoolbox_path = str(Path("src/matlab/mirtoolbox").resolve())
            cls._engine.addpath(
                cls._engine.genpath(mirtoolbox_path),
                nargout=0
            )
            cls._path_added = True

        return cls._engine

# =========================================================================== #
class MIRtoolboxOnsets(MIRtoolboxBaseExtractor):
    FEATURE = ONSET_DETECTION

    ALGO = AlgorithmMeta(
        name="onset_detect",
        tool="mirtoolbox",
        version="1",
        description="Detects onsets (note/chord start times) in audio files using MIRToolbox.",
    )

    INPUT_DOMAIN = InputDomain.AUDIO
    REQUIRED_PACKAGES = ("matlabengine", )
    DEFAULT_PARAMETERS = {}

    @property
    def output(self) -> FeatureOutput:
        return N_ONSETS_OUTPUT

    def extract(self, input_file: Path):
        eng = self.get_engine()
        eng.eval("set(0,'DefaultFigureVisible','off');", nargout=0)
        eng.eval("warning('off','MATLAB:HandleGraphics:ObsoletedProperty:JavaFrame');", nargout=0)
        eng.eval(
            "mirevents_val = mirgetdata(mirevents('" + input_file + "'))",
            nargout = 0
        )
        return len(eng.workspace['mirevents_val'])

# =========================================================================== #
class MIRtoolboxRelativeMode(MIRtoolboxBaseExtractor):
    FEATURE = RELATIVE_MODE

    ALGO = AlgorithmMeta(
        name="relative_mode",
        tool="mirtoolbox",
        version="1",
        description="Computes the majorness/minorness of a piece using MIRToolbox.",
    )

    INPUT_DOMAIN = InputDomain.AUDIO
    REQUIRED_PACKAGES = ("pyramidi", "matlabengine", )
    DEFAULT_PARAMETERS = {"keyfinding_weights": "Gomez_MIRtoolbox"}

    @property
    def output(self) -> FeatureOutput:
        return MIRMODE_OUTPUT

    def extract(self, input_file: Path):
        from pyramidi.models.krumhansl90 import keyfinding, mirmode
    
        eng = self.get_engine()
        eng.eval("set(0,'DefaultFigureVisible','off');", nargout=0)
        eng.eval("warning('off','MATLAB:HandleGraphics:ObsoletedProperty:JavaFrame');", nargout=0)
        eng.eval( "mirchromagram_val = mirgetdata(mirchromagram('" + input_file + "'))", nargout = 0 )
        out = eng.workspace['mirchromagram_val']
        chroma = {i: v[0] for i, v in enumerate(out)}
        key_coefis = keyfinding(chroma, self.parameters["keyfinding_weights"])
        return mirmode(key_coefis)

# =========================================================================== #
