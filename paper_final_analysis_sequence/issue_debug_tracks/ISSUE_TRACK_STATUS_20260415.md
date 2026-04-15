# Issue Track Status

이 문서는 `issue_debug_tracks` 아래에 흩어진 problem/debug 문서를 현재 paper-final 관점에서 다시 읽을 수 있도록 상태를 정리한 요약본이다.

## Summary

| Track | Status | Headline impact | Current handling |
| --- | --- | --- | --- |
| CP branch mapping mismatch | closed for paper use | closed | LP-anchor + same/flip relabel로 manuscript-facing branch 의미를 고정했다. |
| Patch CP effective over-correction | open but bounded | supplement only | `gamma_hat_c_cp_eff`는 supplement만 유지하고 headline은 raw-primary로 고정했다. |
| CP metal-floor cross-check | supplementary cross-check | none | hardware floor를 보는 보조 지표로만 사용한다. |
| Residual 3-way comparison | adopted | supports raw-primary | raw / eff / metal-floor의 역할 분리가 문서와 CSV에 반영됐다. |
| Raw-primary dual reporting | adopted as headline | authoritative | Stage 4 headline은 same-angle raw-primary 기준으로만 읽는다. |
| Eff mechanism root-cause audit | mechanism documented | explains supplement limit | LoS epsilon proxy와 reflective leakage의 구조적 mismatch를 원인으로 문서화했다. |

## Interpretation

### 1. Closed enough for manuscript use

- `CP branch mapping mismatch`
  - 더 이상 headline을 막는 이슈가 아니다.
  - Stage 2 same/flip relabel, Stage 3 LP-anchor lock, direct CP one-point sanity가 함께 convention ambiguity를 닫았다.

### 2. Open, but no longer headline-blocking

- `Patch CP effective over-correction`
  - 여전히 남아 있는 진짜 물리 이슈다.
  - 다만 이 이슈 때문에 headline을 바꾸는 대신, headline metric을 raw-primary로 내려서 논문 본문을 안정화했다.

### 3. Supplement / audit only

- `CP metal-floor cross-check`
  - 절대 residual이 아니라 normalization cross-check다.
- `Eff mechanism root-cause audit`
  - 문제 원인을 설명해 주는 근거이며, headline source는 아니다.

### 4. Adopted paper policy

- `Residual 3-way comparison`
  - raw = primary
  - eff = supplementary corrected estimate
  - metal-floor = normalization-only cross-check
- `Raw-primary dual reporting`
  - 현재 최종 문서와 figure/table export는 이 정책 위에서만 읽으면 된다.

## Files

- machine-readable manifest:
  - `issue_track_manifest_20260415.csv`
- original track documents:
  - `2026-04-14_*_problem.md`
  - `2026-04-14_*_debug.md`
