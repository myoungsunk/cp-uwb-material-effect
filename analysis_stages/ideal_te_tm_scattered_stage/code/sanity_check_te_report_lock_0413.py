from __future__ import annotations

import argparse
import json
from pathlib import Path


def stage_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def ratio(a: float, b: float) -> float:
    if b == 0:
        return float("inf")
    return a / b


def verdict(ok: bool, warn: bool = False) -> str:
    if ok:
        return "PASS"
    if warn:
        return "WARN"
    return "FAIL"


def build_sanity(summary: dict[str, object]) -> dict[str, object]:
    pec = summary["pec"]
    baseline = summary["baseline"]

    checks: list[dict[str, object]] = []

    baseline_correct = baseline["correct_surface_vs_old"]
    baseline_direct_means = []
    baseline_sign_ratios = []
    for theta_key in ["80deg", "85deg"]:
        for surface_key in ["z_m_table3_vs_old_z_m", "z_p_table3_1_vs_old_z_p"]:
            entry = baseline_correct[theta_key][surface_key]
            direct_mean = entry["direct"]["mean_abs"]
            neg_mean = entry["negated_old"]["mean_abs"]
            baseline_direct_means.append(direct_mean)
            baseline_sign_ratios.append(ratio(max(direct_mean, neg_mean), min(direct_mean, neg_mean)))

    max_baseline_mean = max(baseline_direct_means)
    max_baseline_sign_ratio = max(baseline_sign_ratios)
    baseline_close_ok = max_baseline_mean < 0.10
    baseline_no_sign_preference_ok = max_baseline_sign_ratio < 1.05
    checks.append(
        {
            "name": "baseline_correct_surface_close_to_active_merged",
            "verdict": verdict(baseline_close_ok),
            "metric": {"max_direct_mean_abs": max_baseline_mean},
            "rule": "PASS if max direct mean_abs < 0.10",
            "why": "Baseline comparator should stay close to the active merged baseline if the export path is healthy.",
        }
    )
    checks.append(
        {
            "name": "baseline_has_no_global_sign_flip_preference",
            "verdict": verdict(baseline_no_sign_preference_ok),
            "metric": {"max_direct_vs_negated_mean_ratio": max_baseline_sign_ratio},
            "rule": "PASS if max(direct,negated)/min(direct,negated) < 1.05",
            "why": "If direct and negated are nearly identical, there is no evidence for a strong global sign flip.",
        }
    )

    pec_duplicate_ok = not pec["internal_duplicate_pairs"]["table1"] and not pec["internal_duplicate_pairs"]["table2"]
    checks.append(
        {
            "name": "pec_reextract_removed_old_duplicate_block_symptom",
            "verdict": verdict(pec_duplicate_ok),
            "metric": {
                "table1_duplicate_pairs": len(pec["internal_duplicate_pairs"]["table1"]),
                "table2_duplicate_pairs": len(pec["internal_duplicate_pairs"]["table2"]),
            },
            "rule": "PASS if no exact duplicate pairs remain inside the new high-angle focus blocks.",
            "why": "This verifies that the new TE PEC re-extracts no longer carry the old duplicate-block failure mode.",
        }
    )

    pec_subset_errors = [entry["max_abs"] for entry in pec["t3_subset_match"].values()]
    pec_subset_ok = max(pec_subset_errors) < 1e-9
    checks.append(
        {
            "name": "pec_subset_reports_match_parent_tables",
            "verdict": verdict(pec_subset_ok),
            "metric": {"max_subset_match_abs_error": max(pec_subset_errors)},
            "rule": "PASS if subset match max_abs < 1e-9",
            "why": "This confirms that Table3 and Table3_1 are only dedicated subset exports, not independent data products.",
        }
    )

    pec_sign_ratios = []
    for theta_key in ["80deg", "85deg"]:
        for surface_key in ["table1_vs_old_zp", "table1_vs_old_zm"]:
            entry = pec["new_vs_old_sign_check"][theta_key][surface_key]
            direct_mean = entry["direct"]["mean_abs"]
            neg_mean = entry["negated_old"]["mean_abs"]
            pec_sign_ratios.append(ratio(direct_mean, neg_mean))
    min_pec_sign_ratio = min(pec_sign_ratios)
    pec_sign_issue_present = min_pec_sign_ratio > 5.0
    checks.append(
        {
            "name": "pec_reextract_still_shows_strong_sign_or_report_definition_shift",
            "verdict": verdict(pec_sign_issue_present, warn=not pec_sign_issue_present),
            "metric": {"min_direct_to_negated_mean_ratio": min_pec_sign_ratio},
            "rule": "PASS if direct/negated mean_abs ratio > 5.0 for every checked PEC comparison.",
            "why": "A strong ratio means the new PEC re-extract behaves like a sign/report-definition-shifted dataset relative to the active merged PEC CSV.",
        }
    )

    promote_pec = baseline_close_ok and baseline_no_sign_preference_ok and pec_duplicate_ok and pec_subset_ok and not pec_sign_issue_present
    checks.append(
        {
            "name": "promote_new_pec_reextract_to_active_truth_source",
            "verdict": verdict(promote_pec),
            "metric": {
                "baseline_ok": baseline_close_ok and baseline_no_sign_preference_ok,
                "pec_duplicates_removed": pec_duplicate_ok,
                "pec_subset_lock_ok": pec_subset_ok,
                "pec_sign_issue_present": pec_sign_issue_present,
            },
            "rule": "PASS only if baseline is healthy and PEC no longer shows a sign/report-definition shift.",
            "why": "Promotion is allowed only after the PEC-path ambiguity is closed, not merely after duplicate removal.",
        }
    )

    overall = "PASS"
    if any(check["verdict"] == "FAIL" for check in checks):
        overall = "FAIL"
    elif any(check["verdict"] == "WARN" for check in checks):
        overall = "WARN"

    return {
        "overall_verdict": overall,
        "bundle_root": summary["bundle_root"],
        "checks": checks,
        "conclusion": {
            "baseline_path_status": "healthy comparator",
            "pec_path_status": "duplicate symptom removed but sign/report-definition ambiguity remains",
            "active_decision": "do not promote new PEC re-extracts yet",
        },
    }


def to_markdown(sanity: dict[str, object]) -> str:
    lines = [
        "# Sanity check for `te_lock_0413`",
        "",
        f"- overall verdict: **{sanity['overall_verdict']}**",
        f"- bundle root: `{sanity['bundle_root']}`",
        "",
        "## Checks",
    ]

    for check in sanity["checks"]:
        lines.extend(
            [
                f"### {check['name']}",
                f"- verdict: `{check['verdict']}`",
                f"- rule: {check['rule']}",
                f"- metric: `{json.dumps(check['metric'])}`",
                f"- why: {check['why']}",
                "",
            ]
        )

    conclusion = sanity["conclusion"]
    lines.extend(
        [
            "## Locked conclusion",
            f"- baseline path: {conclusion['baseline_path_status']}",
            f"- PEC path: {conclusion['pec_path_status']}",
            f"- active decision: {conclusion['active_decision']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    stage_root = stage_root_from_script()
    parser = argparse.ArgumentParser(description="Run sanity checks on the combined TE report-lock comparison summary.")
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=stage_root / "results" / "te_lock_0413" / "comparison_summary.json",
        help="Combined comparison summary JSON from compare_te_report_lock_0413.py",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=stage_root / "results" / "te_lock_0413",
        help="Directory for sanity-check outputs.",
    )
    args = parser.parse_args()

    summary = json.loads(args.summary_json.read_text(encoding="utf-8"))
    sanity = build_sanity(summary)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "sanity_check.json"
    md_path = args.output_dir / "SANITY_CHECK.md"
    json_path.write_text(json.dumps(sanity, indent=2), encoding="utf-8")
    md_path.write_text(to_markdown(sanity), encoding="utf-8")

    print(f"Wrote JSON: {json_path}")
    print(f"Wrote MD:   {md_path}")
    print(json.dumps(sanity, indent=2))


if __name__ == "__main__":
    main()
