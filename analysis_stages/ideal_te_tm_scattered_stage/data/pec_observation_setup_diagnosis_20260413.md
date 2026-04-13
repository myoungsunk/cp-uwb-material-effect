# PEC Observation Setup Diagnosis (2026-04-13)

## 목적

- `ideal_te_tm_scattered_stage`에서 material 관찰 셋업을 확정하기 위한 PEC 진단 결과 정리
- 판정 기준:
  - baseline 데이터가 clean해야 함
  - PEC에서 `R_TE -> -1`, `R_TM -> +1`, `T -> 0`에 충분히 가까워야 함
- strict PEC-like 기준:
  - `|R_TE + 1| <= 0.1`
  - `|R_TM - 1| <= 0.1`
  - `|T_TE| <= 0.1`
  - `|T_TM| <= 0.1`

## 사용한 데이터 묶음

1. baseline check
   - `1.TE_baseline`
   - `1.TM_baseline`
2. 초기 PEC 비교
   - `500 mm`
   - `1000 mm`
3. wide-plane PEC scan
   - `w_plane = 2000 / 3000 / 4000 mm`
   - `k_obs = 1 / 2 / 3 / 4 / 5`
4. retry3 PEC scan
   - `w_plane = 4000 / 5000 / 6000 mm`
   - `k_obs = 5`
   - `theta = 10 ~ 70 deg`, step `5 deg`

## 1. Baseline 진단

### 결과

- baseline 데이터는 clean함
- `baseline_residual_over_incident`:
  - rows: `196`
  - mean: `9.6e-5`
  - max: `5.71e-4`
- `duplicate_point_id_count`: 전부 `ok`
- `point_id_order_match`: 전부 `ok`
- `xyz_grid_match`: 전부 `ok`
- `unexpected_point_count`: 전부 `ok`
- 메타 field type도 전부 `ScatteredFields` / `scattered_candidate`

### 해석

- baseline 자체는 관찰 셋업 선정의 병목이 아님
- 이후 결정 기준은 사실상 PEC 만족도만 보면 됨

## 2. 초기 PEC 비교: 500 mm vs 1000 mm

### 결과 요약

- `1000 mm`가 `500 mm`보다 명확히 더 PEC-like
- 하지만 strict PEC-like 기준으로 보면 `500 / 1000 mm` 모두 최종 reference로는 부족
- 특히 `TE` 고각에서 `|R_TE + 1|`와 `|T_TE|`가 계속 남음
- `TM`은 비교적 빨리 안정화되지만, `TE`가 병목

### fail 분포

- `500 mm`: `pec_locked_reflection_target_error` fail `25건`
  - `TE 20건`, `TM 5건`
- `1000 mm`: `pec_locked_reflection_target_error` fail `15건`
  - `TE 14건`, `TM 1건`

### 해석

- `1000 mm`는 `500 mm`보다 낫지만, material 관찰용 최종 PEC reference로 확정하기에는 부족
- 이 단계에서 이미 `TE 고각`이 주요 병목이라는 점이 확인됨

## 3. Wide-Plane Scan: 2000 / 3000 / 4000 mm, k_obs = 1..5

### 결과 요약

- `2000 / 3000 / 4000 mm`로 넓히면서 PEC 품질이 크게 개선됨
- `pec_locked_reflection_target_error` fail은 총 `9건`, 전부 `TE`
- `TM` fail은 `0건`

### strict PEC-like 판정

#### theta <= 50 deg

- `3000 mm`: 모든 `k_obs` 통과
- `4000 mm`: 모든 `k_obs` 통과
- `2000 mm`: `k_obs = 3, 4`는 `T_TE` 때문에 탈락

#### theta <= 60 deg

- `4000 mm`: 모든 `k_obs` 통과
- `3000 mm`: `k_obs = 1, 2, 3, 4` 통과
- `3000 mm, k_obs = 5`: `T_TE`가 약간 큼
- `2000 mm`: `TE` residual 때문에 불안정

#### theta <= 70 deg

- 완전 통과 셋업 없음
- 병목은 여전히 `TE 70 deg`
- 즉, plane을 키워도 `TE 70 deg`까지 strict PEC truth로 쓰기엔 부족

### 해석

- `4000 mm`부터는 `theta <= 60 deg` 범위에서 관찰 셋업으로 쓸 수 있는 수준으로 들어옴
- 다만 `70 deg TE`는 여전히 unresolved

## 4. Retry3: k_obs = 5 고정, 4000 / 5000 / 6000 mm

### 데이터 의미

- 기존 wide-plane 결과에서 `k_obs = 5`가 유력 후보였기 때문에
- `k_obs = 5`를 고정하고 `w_plane = 4000 / 5000 / 6000 mm`를 더 정밀하게 비교함
- `theta`도 `5 deg` 간격으로 더 촘촘하게 재평가함

### 핵심 결과

#### 4000 mm / k_obs = 5

- `pec_locked_reflection_target_error` fail `1건`
  - `TE 70 deg`, `|R_TE + 1| = 0.128684`
- `pec_abs_T_TE` warn `2건`
  - `TE 65 deg`: `|T_TE| = 0.113645`
  - `TE 70 deg`: `|T_TE| = 0.128817`
- `passivity_excess` warn `9건`

#### 5000 mm / k_obs = 5

- `pec_locked_reflection_target_error` fail `0건`
- `passivity_excess` warn `0건`
- `pec_abs_T_TE` warn `1건`
  - `TE 65 deg`: `|T_TE| = 0.109241`
- `TE 70 deg`는 통과권 안쪽
  - `|R_TE + 1| = 0.079559`
  - `|T_TE| = 0.099207`

#### 6000 mm / k_obs = 5

- `pec_locked_reflection_target_error` fail `0건`
- `pec_abs_T_TE` warn `2건`
  - `TE 65 deg`: `|T_TE| = 0.102885`
  - `TE 70 deg`: `|T_TE| = 0.125285`
- `passivity_excess` warn `2건`
  - `TM 10 deg`
  - `TM 15 deg`

### strict PEC-like 판정

#### theta <= 50 deg

- `4000 / 5000 / 6000 mm`, 모두 strict PEC-like 통과

#### theta <= 60 deg

- `4000 / 5000 / 6000 mm`, 모두 strict PEC-like 통과

#### theta <= 65 deg

- 완전 통과 셋업 없음
- 이유는 모두 `TE transmission residual`

#### theta <= 70 deg

- 완전 통과 셋업 없음
- 그래도 best compromise는 `5000 mm / k_obs = 5`

### 왜 5000 / 5를 최종 권고로 보는가

- `4000 / 5`:
  - reflection fail `1건`
  - passivity warn 많음
- `5000 / 5`:
  - reflection fail `0건`
  - passivity warn `0건`
  - 남는 문제는 `TE 65 deg`의 `T_TE` 1건뿐
- `6000 / 5`:
  - reflection fail은 없지만
  - `TE 65 / 70 deg`에서 `T_TE` warn이 2건
  - `TM 10 / 15 deg` passivity warn도 2건

즉, `6000 / 5`가 "실패한 셋업"은 아니지만, 전체 균형은 `5000 / 5`가 더 좋음.

## 최종 결론

### material 관찰 셋업 권고

- 최종 권고 셋업:
  - `w_plane = 5000 mm`
  - `k_obs = 5`

### 권고 해석 범위

- 안전하게 확정 가능한 범위:
  - `TM: 10 ~ 70 deg`
  - `TE: 10 ~ 60 deg`
- `TE 65 deg`:
  - 거의 경계선
  - `5000 / 5`에서 `|T_TE| = 0.109241`
- `TE 70 deg`:
  - `5000 / 5`가 가장 나은 타협안이지만
  - strict PEC truth로 완전히 확정됐다고 보긴 어려움

### 실무용 문장

- material 분석 기본 셋업은 `5000 mm / k_obs = 5`로 고정
- 기본 해석 범위는 `TM 전각 + TE 60 deg 이하`
- `TE 65 / 70 deg`는 "near-limit" 또는 "reference caution"으로 별도 표기하는 것이 안전

## 참고 결과 파일

- baseline
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/baseline_actual1mm_20260413_scattered/qc_report.csv`
- 초기 PEC
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/copy2_priority_pec_20260413_scattered/qc_report.csv`
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/copy2_priority_pec_20260413_scattered/truth_table_linear_locked.csv`
- wide-plane
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/copy2_pec_wide_plane_20260413_scattered/qc_report.csv`
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/copy2_pec_wide_plane_20260413_scattered/truth_table_linear_locked.csv`
- retry3
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/copy2_pec_kobs5_wide_plane_retry3_20260413_scattered/qc_report.csv`
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/copy2_pec_kobs5_wide_plane_retry3_20260413_scattered/truth_table_linear_locked.csv`

