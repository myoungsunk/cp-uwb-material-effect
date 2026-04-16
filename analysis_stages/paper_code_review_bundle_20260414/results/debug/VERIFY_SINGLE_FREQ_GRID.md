# Verify Single-Frequency Residual Grid

Execution date: `2026-04-16`

## Scope

- Requested grid points: `5.0 / 6.5 / 8.0 GHz`.
- Current Stage 3 frequency-resolved bundle spans `6.24 GHz` to `6.74 GHz`.
- Replay therefore uses the nearest in-band points: `6.24 / 6.50 / 6.74 GHz`.
- Stage 1 and Stage 2 ideal truth tables are currently available at: `6.24 GHz, 6.50 GHz, 6.74 GHz`.
- Band-average baseline stays anchored to the nearest available ideal reference at `6.50 GHz`.

## Frequency Mapping

- requested `5.00 GHz` -> actual `6.24 GHz` (lower_band_edge), ideal-match-available=True
- requested `6.50 GHz` -> actual `6.50 GHz` (center_near_6p5), ideal-match-available=True
- requested `8.00 GHz` -> actual `6.74 GHz` (upper_band_edge), ideal-match-available=True

## Per-Frequency Replay

- `6.24 GHz`: raw=`1`, eff=`9`, LP=`12`, all-zero-pass=`False`
- `6.50 GHz`: raw=`0`, eff=`15`, LP=`15`, all-zero-pass=`False`
- `6.74 GHz`: raw=`0`, eff=`12`, LP=`12`, all-zero-pass=`False`

## Band-Average Baseline

- main-range raw ordering violations: `0`
- main-range eff ordering violations: `8`
- main-range LP ordering violations: `15`

## 6.50 GHz Replay

- raw ordering violations: `0`
- eff ordering violations: `15`
- LP ordering violations: `15`
- pass criterion met: `False`

## Interpretation

- At 6.50 GHz the ordering violations do not collapse to zero, so band averaging alone is not sufficient to explain the Stage 4 violation pattern.
- In particular, the eff path remains at `15` violation row(s), compared with the band-mean baseline `8`.

## 6.50 GHz Eff Violations

- concrete 35 deg: ideal=0.072142, eff=0.030496, Delta(ideal-eff)=-7.48 dB
- concrete 40 deg: ideal=0.089183, eff=0.033421, Delta(ideal-eff)=-8.53 dB
- concrete 45 deg: ideal=0.139125, eff=0.053838, Delta(ideal-eff)=-8.25 dB
- concrete 50 deg: ideal=0.168357, eff=0.084662, Delta(ideal-eff)=-5.97 dB
- concrete 55 deg: ideal=0.176088, eff=0.121806, Delta(ideal-eff)=-3.20 dB
- glass 35 deg: ideal=0.082523, eff=0.053085, Delta(ideal-eff)=-3.83 dB
- glass 40 deg: ideal=0.090817, eff=0.045312, Delta(ideal-eff)=-6.04 dB
- glass 45 deg: ideal=0.148479, eff=0.059917, Delta(ideal-eff)=-7.88 dB
- glass 50 deg: ideal=0.174348, eff=0.070289, Delta(ideal-eff)=-7.89 dB
- glass 55 deg: ideal=0.217301, eff=0.113869, Delta(ideal-eff)=-5.61 dB
- glass 60 deg: ideal=0.266128, eff=0.170559, Delta(ideal-eff)=-3.86 dB
- wood 25 deg: ideal=0.023293, eff=0.017270, Delta(ideal-eff)=-2.60 dB
- wood 30 deg: ideal=0.035412, eff=0.011466, Delta(ideal-eff)=-9.79 dB
- wood 35 deg: ideal=0.067205, eff=0.026866, Delta(ideal-eff)=-7.96 dB
- wood 45 deg: ideal=0.120142, eff=0.062141, Delta(ideal-eff)=-5.73 dB

## Outputs

- Frequency mapping CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_single_freq_grid_mapping.csv`
- Full replay CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_single_freq_grid_full.csv`
- Summary CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_single_freq_grid_summary.csv`
