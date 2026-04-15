# Consolidated review copy for paper-pipeline code assessment.
# Stage: 1
# Role: Stage 1 wrapper entrypoint that calls the ideal truth-table builder.
# Source: analysis_stages/ideal_te_tm_scattered_stage/code/te_tm_extraction_ideal_plane_wave.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

import importlib.util
from pathlib import Path


def load_main():
    try:
        from stage_1_build_truth_table import main as entry_main

        return entry_main
    except ModuleNotFoundError:
        module_path = Path(__file__).resolve().with_name("stage_1_build_truth_table.py")
        if not module_path.exists():
            raise
        spec = importlib.util.spec_from_file_location("stage_1_build_truth_table", module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Could not load stage_1_build_truth_table from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.main


if __name__ == "__main__":
    load_main()()
