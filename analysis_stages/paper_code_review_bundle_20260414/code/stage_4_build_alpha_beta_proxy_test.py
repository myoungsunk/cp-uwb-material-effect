# Consolidated review copy for paper-pipeline code assessment.
# Stage: 4
# Role: Build the Stage 4k alpha/beta proxy comparison audit.
# Source: analysis_stages/stage4k_alpha_beta_proxy_test_20260414/code/build_alpha_beta_proxy_test.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

from pathlib import Path

import importlib.util


def load_main():
    source = (
        Path(__file__).resolve().parents[2]
        / "stage4k_alpha_beta_proxy_test_20260414"
        / "code"
        / "build_alpha_beta_proxy_test.py"
    )
    spec = importlib.util.spec_from_file_location("stage4k_alpha_beta_proxy_test", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load source script: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


main = load_main()


if __name__ == "__main__":
    main()
