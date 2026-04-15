# Consolidated review copy for paper-pipeline code assessment.
# Stage: 4
# Role: Build the Stage 4j mismatch-signature audit for eff over-correction.
# Source: analysis_stages/stage4j_eff_mismatch_signature_20260414/code/build_eff_mismatch_signature.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

from pathlib import Path

import importlib.util


def load_main():
    source = (
        Path(__file__).resolve().parents[2]
        / "stage4j_eff_mismatch_signature_20260414"
        / "code"
        / "build_eff_mismatch_signature.py"
    )
    spec = importlib.util.spec_from_file_location("stage4j_eff_mismatch_signature", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load source script: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


main = load_main()


if __name__ == "__main__":
    main()
