# Active OLD M3 Quantitative Report

This report uses the corrected active `OLD M3` dataset that was restored as the
standard reference on 2026-04-10. The values below are not hand-edited
corrections; they come from rerunning the current pipelines with the active
stage-local CSVs.

Machine-readable all-material exports are also available in
`report_data/old_m3_active`:

- `cp_all_materials.csv`
- `lp_all_materials.csv`
- `triple_comparison_all_materials.csv`
- `suppression_gain_long.csv`

## Data Source

- Active CP run:
  `python .\analysis_stages\patch_cp_stage_system\code\gamma_extraction_v2.py`
- Active LP run:
  `python .\analysis_stages\patch_lp_stage_system\code\gamma_extraction_lp.py --with-lp`
- LP metal-plate truth / suppression run:
  `python .\analysis_stages\patch_lp_stage_system\metal_plate_normalized\code\unified_analysis.py`

Interpretation lock:

- `Gamma_X` is the main robust CP result.
- `Gamma_C` is an antenna-limited corrected co-term.
- LP metal-plate normalization is the TE/TM ground truth.
- LP M3-direct is retained as a comparison path, not the final truth path.
- Final suppression claims use LP metal-plate in the numerator and CP corrected
  co-term in the denominator.

## 1. Antenna Diagnostics From Active M3 Free-Space Data

Reading rule:

- `epsilon(LR/RR)` and `epsilon(RL/LL)` must be `<= -20 dB` for uncorrected
  co-term use.
- Port asymmetry must stay within about `+/- 1 dB` for the reciprocity
  estimator to cancel antenna asymmetry cleanly.

| theta_i | alpha | epsilon(LR/RR) [dB] | epsilon(RL/LL) [dB] | Port Asym [dB] | A1 | A2 |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | 80 | -4.1 | -12.3 | -0.09 | FAIL | PASS |
| 15 | 75 | -4.7 | -11.4 | -0.08 | FAIL | PASS |
| 20 | 70 | -5.4 | -10.9 | -0.07 | FAIL | PASS |
| 25 | 65 | -6.0 | -10.6 | -0.06 | FAIL | PASS |
| 30 | 60 | -6.6 | -10.7 | -0.05 | FAIL | PASS |
| 35 | 55 | -7.1 | -10.9 | -0.04 | FAIL | PASS |
| 40 | 50 | -7.6 | -11.3 | -0.04 | FAIL | PASS |
| 45 | 45 | -8.1 | -11.8 | -0.04 | FAIL | PASS |
| 50 | 40 | -8.7 | -12.5 | -0.03 | FAIL | PASS |
| 55 | 35 | -9.2 | -13.4 | -0.03 | FAIL | PASS |
| 56 | 34 | -9.4 | -13.6 | -0.03 | FAIL | PASS |
| 60 | 30 | -9.9 | -14.4 | -0.02 | FAIL | PASS |
| 65 | 25 | -10.6 | -15.5 | -0.02 | FAIL | PASS |
| 70 | 20 | -11.4 | -16.5 | -0.01 | FAIL | PASS |

Key takeaways:

- `A1` fails at every angle, so co-term correction is mandatory.
- `A2` passes at every angle, with worst port asymmetry only `0.09 dB`.
- This is why `Gamma_X` remains usable while `Gamma_C` must be treated as
  antenna-limited.

The same table is stored in
[report_data/old_m3_active/antenna_diagnostics.csv](D:\OneDrive - postech.ac.kr\명선\2026\3.9 CP odd-bounce\4.CP_material_effect\report_data\old_m3_active\antenna_diagnostics.csv).

## 2. CP Reflection Extraction, Concrete

Definitions:

- `|Gamma_X|`: M3 reciprocity estimator.
- `|Gamma_C_raw|`: raw co-term.
- `|Gamma_C_cor|`: M3 leakage-corrected co-term.
- `|Gamma_X|_met`: metal-plate normalized cross check.
- `XPD_cor > 0 dB`: CP suppression is still effective.

| theta_i | |Gamma_X| | |Gamma_C_raw| | |Gamma_C_cor| | XPD_cor [dB] | |Gamma_X|_met |
| --- | --- | --- | --- | --- | --- |
| 10 | 0.4450 | 0.1084 | 0.1808 | 7.8 | 0.3906 |
| 15 | 0.4277 | 0.1238 | 0.1313 | 10.3 | 0.3922 |
| 20 | 0.3582 | 0.1209 | 0.0786 | 13.2 | 0.3940 |
| 25 | 0.3975 | 0.1447 | 0.0656 | 15.6 | 0.3964 |
| 30 | 0.4288 | 0.1687 | 0.0440 | 19.8 | 0.4002 |
| 35 | 0.3769 | 0.1667 | 0.0280 | 22.6 | 0.4035 |
| 40 | 0.4196 | 0.1944 | 0.0334 | 22.0 | 0.4036 |
| 45 | 0.3899 | 0.2047 | 0.0550 | 17.0 | 0.4039 |
| 50 | 0.4086 | 0.2327 | 0.0832 | 13.8 | 0.3979 |
| 55 | 0.3760 | 0.2506 | 0.1209 | 9.9 | 0.3902 |
| 56 | 0.3756 | 0.2571 | 0.1294 | 9.3 | 0.3880 |
| 60 | 0.3829 | 0.2928 | 0.1707 | 7.0 | 0.3760 |
| 65 | 0.3547 | 0.3316 | 0.2286 | 3.8 | 0.3562 |
| 70 | 0.3198 | 0.3867 | 0.3044 | 0.4 | 0.3288 |

Interpretation:

- Concrete cross reflection stays fairly stable.
- Corrected co-term is smallest around `30-40 deg`, where XPD also peaks.
- `XPD_cor` reaches `22.6 dB` at `35 deg` and drops toward `0 dB` by `70 deg`.
- The metal-normalized cross check remains flat through the main useful angle
  region, which supports the stability of `Gamma_X`.

The same table is stored in
[report_data/old_m3_active/cp_concrete.csv](D:\OneDrive - postech.ac.kr\명선\2026\3.9 CP odd-bounce\4.CP_material_effect\report_data\old_m3_active\cp_concrete.csv).

## 3. LP Reflection Extraction, Concrete

Definitions:

- `LP M3`: unfolded free-space reference.
- `LP met`: metal-plate normalization.
- `Delta_met`: LP metal-plate result minus Fresnel slab reference.

`56 deg` is not included here because the active LP-direct M3 dataset is a
13-angle sweep without that sample.

| theta_i | |R_TE|_M3 | |R_TE|_met | |R_TE|_Fresnel | Delta_met [dB] | |R_TM|_M3 | |R_TM|_met | |R_TM|_Fresnel | Delta_met [dB] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | 0.4238 | 0.3958 | 0.3970 | -0.0 | 0.5560 | 0.3857 | 0.3865 | -0.0 |
| 15 | 0.4150 | 0.4037 | 0.4043 | -0.0 | 0.5218 | 0.3799 | 0.3805 | -0.0 |
| 20 | 0.3607 | 0.4148 | 0.4148 | -0.0 | 0.4185 | 0.3697 | 0.3717 | -0.0 |
| 25 | 0.4082 | 0.4297 | 0.4286 | 0.0 | 0.4511 | 0.3580 | 0.3599 | -0.0 |
| 30 | 0.4548 | 0.4473 | 0.4457 | 0.0 | 0.4545 | 0.3433 | 0.3443 | -0.0 |
| 35 | 0.4259 | 0.4692 | 0.4659 | 0.1 | 0.3632 | 0.3220 | 0.3239 | -0.1 |
| 40 | 0.4907 | 0.4953 | 0.4891 | 0.1 | 0.3740 | 0.2960 | 0.2976 | -0.0 |
| 45 | 0.4922 | 0.5209 | 0.5151 | 0.1 | 0.2965 | 0.2618 | 0.2641 | -0.1 |
| 50 | 0.5476 | 0.5551 | 0.5446 | 0.2 | 0.2683 | 0.2218 | 0.2224 | -0.0 |
| 55 | 0.5574 | 0.5885 | 0.5783 | 0.2 | 0.1830 | 0.1664 | 0.1710 | -0.2 |
| 60 | 0.6217 | 0.6294 | 0.6177 | 0.2 | 0.1225 | 0.1064 | 0.1082 | -0.1 |
| 65 | 0.6570 | 0.6795 | 0.6635 | 0.2 | 0.0378 | 0.0341 | 0.0340 | 0.0 |
| 70 | 0.6987 | 0.7315 | 0.7163 | 0.2 | 0.0898 | 0.0852 | 0.0774 | 0.8 |

Interpretation:

- LP metal-plate stays within about `+/- 0.2 dB` for `R_TE`.
- LP metal-plate stays within about `-0.2 ~ +0.8 dB` for `R_TM`.
- LP M3-direct preserves the trend but overestimates `R_TM`, which is why LP
  metal-plate is the final TE/TM ground truth.

The same table is stored in
[report_data/old_m3_active/lp_concrete.csv](D:\OneDrive - postech.ac.kr\명선\2026\3.9 CP odd-bounce\4.CP_material_effect\report_data\old_m3_active\lp_concrete.csv).

## 4. Triple Comparison, Concrete

Comparison:

- LP metal-plate direct: ground truth.
- CP M3-derived: `Gamma_X +/- Gamma_C`.
- Fresnel slab: theory reference.

| theta_i | LP R_TE | CP R_TE | Fresnel R_TE | LP R_TM | CP R_TM | Fresnel R_TM |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | 0.3958 | 0.6256 | 0.3970 | 0.3857 | 0.2646 | 0.3865 |
| 15 | 0.4037 | 0.5590 | 0.4043 | 0.3799 | 0.2965 | 0.3805 |
| 20 | 0.4148 | 0.4361 | 0.4148 | 0.3697 | 0.2806 | 0.3717 |
| 25 | 0.4297 | 0.4601 | 0.4286 | 0.3580 | 0.3360 | 0.3599 |
| 30 | 0.4473 | 0.4677 | 0.4457 | 0.3433 | 0.3910 | 0.3443 |
| 35 | 0.4692 | 0.3836 | 0.4659 | 0.3220 | 0.3722 | 0.3239 |
| 40 | 0.4953 | 0.4069 | 0.4891 | 0.2960 | 0.4344 | 0.2976 |
| 45 | 0.5209 | 0.3439 | 0.5151 | 0.2618 | 0.4381 | 0.2641 |
| 50 | 0.5551 | 0.3326 | 0.5446 | 0.2218 | 0.4870 | 0.2224 |
| 55 | 0.5885 | 0.2590 | 0.5783 | 0.1664 | 0.4949 | 0.1710 |
| 60 | 0.6294 | 0.2136 | 0.6177 | 0.1064 | 0.5530 | 0.1082 |
| 65 | 0.6795 | 0.1267 | 0.6635 | 0.0341 | 0.5832 | 0.0340 |
| 70 | 0.7315 | 0.0217 | 0.7163 | 0.0852 | 0.6240 | 0.0774 |

Interpretation:

- LP follows Fresnel closely at every angle.
- CP is acceptable around `25-35 deg`.
- Beyond `45 deg`, `R_TE` is underestimated while `R_TM` is overestimated.
- The paired error comes from the corrected co-term entering `R_TE` and `R_TM`
  with opposite signs.

The same table is stored in
[report_data/old_m3_active/triple_comparison_concrete.csv](D:\OneDrive - postech.ac.kr\명선\2026\3.9 CP odd-bounce\4.CP_material_effect\report_data\old_m3_active\triple_comparison_concrete.csv).

## 5. CP Multipath Suppression Gain Over LP

Definition:

`G_supp = 20 log10( max(|R_TE|, |R_TM|)_LP / |Gamma_C_cor|_CP )`

- Numerator: LP metal-plate worst-case co-pol reflection.
- Denominator: CP corrected co-pol residual.
- Larger values mean stronger CP advantage against single-bounce multipath.

| theta_i | Concrete [dB] | Glass [dB] | Wood [dB] | Average [dB] |
| --- | --- | --- | --- | --- |
| 10 | 6.8 | 6.6 | 7.2 | 6.9 |
| 15 | 9.8 | 9.6 | 10.6 | 10.0 |
| 20 | 14.5 | 14.3 | 15.8 | 14.8 |
| 25 | 16.3 | 15.4 | 19.6 | 17.1 |
| 30 | 20.1 | 18.8 | 23.8 | 20.9 |
| 35 | 24.5 | 24.0 | 22.0 | 23.5 |
| 40 | 23.4 | 24.7 | 17.1 | 21.7 |
| 45 | 19.5 | 21.5 | 14.1 | 18.4 |
| 50 | 16.5 | 18.5 | 11.1 | 15.4 |
| 55 | 13.7 | 15.1 | 9.3 | 12.7 |
| 56 | 13.3 | 14.5 | 8.9 | 12.2 |
| 60 | 11.3 | 12.3 | 7.3 | 10.3 |
| 65 | 9.5 | 10.2 | 6.0 | 8.6 |
| 70 | 7.6 | 8.3 | 4.7 | 6.9 |

Key conclusions:

- The main `25-40 deg` region gives about `15-25 dB` suppression gain.
- Peak gain:
  glass `24.7 dB @ 40 deg`, concrete `24.5 dB @ 35 deg`,
  wood `23.8 dB @ 30 deg`.
- Gain decreases beyond about `55 deg` as Brewster behavior reduces the CP
  advantage.
- Even at `10-15 deg`, CP still keeps about `7-10 dB` average benefit.

This table is stored in
[report_data/old_m3_active/suppression_gain.csv](D:\OneDrive - postech.ac.kr\명선\2026\3.9 CP odd-bounce\4.CP_material_effect\report_data\old_m3_active\suppression_gain.csv).

## 6. Final Reporting Guidance

Recommended reporting structure for the active dataset:

- Use `Gamma_X` and reflected `XPD` as the main CP claims.
- Use LP metal-plate TE/TM as the ground truth for Fresnel and Brewster
  validation.
- Use `G_supp` as the main quantitative reason CP-UWB helps indoor positioning.
- Do not promote CP-derived `R_TE/R_TM` to material truth at large angle.
- Keep the current `OLD M3` dataset as the final claim basis; treat the newer
  replacement M3 only as an archived debug comparison.

## 7. Related Result Folders

- CP stage figures:
  [results](D:\OneDrive - postech.ac.kr\명선\2026\3.9 CP odd-bounce\4.CP_material_effect\analysis_stages\patch_cp_stage_system\results)
- LP-direct figures:
  [results](D:\OneDrive - postech.ac.kr\명선\2026\3.9 CP odd-bounce\4.CP_material_effect\analysis_stages\patch_lp_stage_system\results)
- LP metal-plate truth / suppression figures:
  [results](D:\OneDrive - postech.ac.kr\명선\2026\3.9 CP odd-bounce\4.CP_material_effect\analysis_stages\patch_lp_stage_system\metal_plate_normalized\results)
