class MIRtoolboxOnsets(FeatureExtractor):
    FEATURE = ONSET_DETECTION

    ALGO = AlgorithmMeta(
        name="onset_detect",
        tool="mirtoolbox",
        version="1",
        description=(
        ),
    )

    INPUT_DOMAIN = InputDomain.AUDIO
    REQUIRED_PACKAGES = ()
    DEFAULT_PARAMETERS = {}

    @property
    def output(self) -> FeatureOutput:
        return N_ONSETS_OUTPUT

    def extract(self, input_file: Path):
        return

# =========================================================================== #