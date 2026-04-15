# Consolidated review copy for paper-pipeline code assessment.
# Stage: 3
# Role: Build the metal leakage proxy audit used by later eff-mismatch analyses.
# Source: analysis_stages/stage3_metal_leakage_proxy_audit_20260414/code/build_metal_leakage_proxy_audit.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

from pathlib import Path

import importlib.util


def load_main():
    source = (
        Path(__file__).resolve().parents[2]
        / "stage3_metal_leakage_proxy_audit_20260414"
        / "code"
        / "build_metal_leakage_proxy_audit.py"
    )
    spec = importlib.util.spec_from_file_location("stage3_metal_leakage_proxy_audit", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load source script: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


main = load_main()


if __name__ == "__main__":
    main()
