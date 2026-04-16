from __future__ import annotations

import argparse
from pathlib import Path

from audit_coherent_vs_incoherent import PASS_GAP_DB, run_audit


def build_argparser() -> argparse.ArgumentParser:
    bundle_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description=(
            "Replay coherent vs incoherent band averaging using existing Stage 3 "
            "frequency-resolved CP/LP exports."
        )
    )
    parser.add_argument(
        "--patch-cp-freq",
        type=Path,
        default=bundle_root / "data" / "stage_3" / "cp" / "patch_cp_extracted_freq_resolved.csv",
    )
    parser.add_argument(
        "--patch-lp-freq",
        type=Path,
        default=bundle_root / "data" / "stage_3" / "lp" / "patch_lp_extracted_freq_resolved.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=bundle_root / "results" / "debug",
    )
    parser.add_argument(
        "--include-metal",
        action="store_true",
        help="Include metal reference rows in the replay outputs.",
    )
    parser.add_argument(
        "--restrict-stage4-main-range",
        action="store_true",
        help="Limit the replay to the Stage 4 main range instead of all locked angles.",
    )
    return parser


def main() -> None:
    args = build_argparser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    scope_lines = [
        "- Replay from existing Stage 3 frequency-resolved exports only.",
        "- Incoherent band mean: `mean(|x(f)|)`.",
        "- Coherent band mean: `|mean(x(f))|`.",
        f"- Materials included: `{'metal, concrete, glass, wood' if args.include_metal else 'concrete, glass, wood'}`.",
        (
            "- Angle filter: Stage 4 main range only "
            "(`20 deg <= theta <= material-specific VALID_MAX`)."
            if args.restrict_stage4_main_range
            else "- Angle filter: all locked angle rows retained."
        ),
        f"- Pass criterion: incoherent-coherent gap `>= {PASS_GAP_DB:.1f} dB`.",
    ]
    outputs = run_audit(
        patch_cp_path=args.patch_cp_freq,
        patch_lp_path=args.patch_lp_freq,
        output_dir=args.output_dir.resolve(),
        include_metal=args.include_metal,
        restrict_stage4_main_range=args.restrict_stage4_main_range,
        repo_root=repo_root,
        detail_filename="verify_coherent_vs_incoherent.csv",
        summary_filename="verify_coherent_vs_incoherent_summary_by_material.csv",
        rollup_filename="verify_coherent_vs_incoherent_material_rollup.csv",
        md_filename="VERIFY_COHERENT_VS_INCOHERENT.md",
        md_title="Verify Coherent vs Incoherent Band Average",
        scope_lines=scope_lines,
    )

    print(f"Wrote {outputs['detail']}")
    print(f"Wrote {outputs['summary']}")
    print(f"Wrote {outputs['rollup']}")
    print(f"Wrote {outputs['md']}")


if __name__ == "__main__":
    main()
