import re
from typing import Union

# Shorthand map for known transform types
TYPE_SHORTHANDS = {
    "TransformPitch": "pitch",
    "TransformTempo": "tempo",
    "SetVelocity": "vel",
    "SynthesizeAudio": "synth",
    "PyraMIDIFile": "midi",
}

# Params that are redundant with the type shorthand and can be shown as bare values
REDUNDANT_PARAMS = {
    "TransformPitch": {"amount"},
    "TransformTempo": {"tempo_ratio"},
    "SetVelocity": {"velocity"},
}

SKIP_PARAMS = {
    "TransformPitch": {"method", "min_note", "max_note", "octave_shift"},
}

SKIP_TYPES = {"SynthesizeAudio"}

def _format_value(v) -> str:
    """Round floats, drop Nones, keep everything else compact."""
    if v is None:
        return None  # signal to skip this key entirely
    if isinstance(v, float):
        # Round to 3 sig figs, strip trailing zeros
        rounded = f"{v:.3g}"
        return rounded
    return str(v)

def _spec_to_str(s: Union[str, dict]) -> str:
    if isinstance(s, dict):
        type_name = s.get("type", "")
        short = TYPE_SHORTHANDS.get(type_name, type_name.lower())
        redundant = REDUNDANT_PARAMS.get(type_name, set())
        skip = SKIP_PARAMS.get(type_name, set())

        params = []
        for k, v in s.items():
            if k == "type" or k in skip:
                continue
            formatted = _format_value(v)
            if formatted is not None:
                if k in redundant:
                    params.append(formatted)
                else:
                    short_k = k.replace("soundfont", "sf")
                    params.append(f"{short_k}={formatted}")

        if params:
            return f"{short}({'_'.join(params)})"
        return short
    return str(s)

def filename_from_spec(pipeline, base_name: str = None) -> str:
    specs = pipeline.to_spec()
    parts = [_spec_to_str(s) for s in specs if s.get("type") not in SKIP_TYPES]
    spec_str = "_".join(parts)

    spec_str = re.sub(r"[^a-zA-Z0-9_()\-.]", "_", spec_str)

    max_length = 80
    if len(spec_str) > max_length:
        spec_str = spec_str[:max_length] + "…"

    return f"{base_name}_{spec_str}" if base_name else spec_str
