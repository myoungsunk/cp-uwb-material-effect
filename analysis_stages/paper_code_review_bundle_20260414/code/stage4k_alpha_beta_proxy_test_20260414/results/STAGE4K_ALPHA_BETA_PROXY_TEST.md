# Stage 4k: Alpha/Beta Proxy Test

Tested proxies:
- current: eps_lr_rr = h3_LR / h3_RR
- alternate: eps_rl_ll = h3_RL / h3_LL
- no-phase alpha/beta kernel: alpha + conj(beta)
- phase-fit alpha/beta kernel: alpha + conj(beta) * exp(-2j k d_eff cos(theta)), using the fitted `d_eff`

## Metal leakage match overall (20-55 deg)
                     proxy  mag_ratio_db_mean  mag_ratio_db_abs_mean  phase_diff_deg_abs_p50  phase_diff_deg_abs_p95
                 eps_lr_rr          -3.967485               3.967485               14.471806               22.071916
                 eps_rl_ll           0.192714               0.280246               89.113521               91.460020
kernel_alpha_beta_no_phase          -2.617444               2.617444                7.184578               11.895461
 kernel_alpha_beta_phasefit         -2.556653               2.556653               12.563463               18.940830

Interpretation:
- `eps_rl_ll` fixes the magnitude bias but leaves an approximately 90 degree phase error, so it is not a valid direct replacement.
- `alpha + conj(beta)` improves both magnitude and phase mismatch relative to the current `eps_lr_rr` correction.
- adding the simple phase-fit term reduces the magnitude mismatch slightly further, but does not fully remove the residual high-angle instability.

## Material ideal comparison summary
                         proxy_name material  negative_gap_rows  mean_vs_ideal_db  worst_vs_ideal_db
                    gamma_c_raw_mag concrete                  0         10.451995           2.832956
                    gamma_c_raw_mag    glass                  0          9.423185           0.921292
                    gamma_c_raw_mag     wood                  0          8.653089           0.951045
              gamma_c_eff_lr_rr_mag concrete                  5          2.970880          -8.511229
              gamma_c_eff_lr_rr_mag    glass                  1          8.768160          -2.314543
              gamma_c_eff_lr_rr_mag     wood                  2          6.453285          -6.927326
              gamma_c_eff_rl_ll_mag concrete                  0         12.436388           4.071595
              gamma_c_eff_rl_ll_mag    glass                  0         11.155253           1.321116
              gamma_c_eff_rl_ll_mag     wood                  0         10.415544           1.616477
gamma_c_eff_alpha_beta_no_phase_mag concrete                  6          2.743252          -4.365817
gamma_c_eff_alpha_beta_no_phase_mag    glass                  1          7.350662          -1.008475
gamma_c_eff_alpha_beta_no_phase_mag     wood                  2          5.394111          -3.469831
gamma_c_eff_alpha_beta_phasefit_mag concrete                  5          3.933655          -2.999004
gamma_c_eff_alpha_beta_phasefit_mag    glass                  1          7.496480          -0.834088
gamma_c_eff_alpha_beta_phasefit_mag     wood                  2          5.677229          -1.976752

Interpretation:
- the phase-fit alpha/beta kernel is better than the current `eps_lr_rr` correction and better than the no-phase alpha/beta kernel in the worst-angle rows.
- however, it still leaves negative-gap rows, especially for concrete and wood.
- this means the split-alpha/beta idea is promising, but the current approximation is not yet strong enough to replace `raw` as the paper-primary metric.

## Metal floor by proxy
 theta_deg  raw_mag  eff_lr_rr_mag  eff_rl_ll_mag  eff_alpha_beta_no_phase_mag
      10.0 0.265993       0.474056       0.385083                     0.331475
      15.0 0.290142       0.360370       0.417359                     0.216996
      20.0 0.267058       0.238352       0.374052                     0.136142
      25.0 0.294841       0.229078       0.410375                     0.143157
      30.0 0.315319       0.205616       0.446573                     0.153372
      35.0 0.281671       0.155293       0.382259                     0.111212
      40.0 0.281852       0.174579       0.393814                     0.123176
      45.0 0.263135       0.141467       0.357508                     0.080411
      50.0 0.239990       0.166296       0.334233                     0.074476
      55.0 0.218737       0.147880       0.293105                     0.041047
      56.0 0.214554       0.146528       0.290616                     0.040113
      60.0 0.192193       0.289383       0.276963                     0.187168
      65.0 0.164276       0.336400       0.233575                     0.236878
      70.0 0.149791       0.220456       0.207980                     0.154255

Phase-fit floor:

 theta_deg  eff_alpha_beta_phasefit_mag
      10.0                     0.294052
      15.0                     0.194941
      20.0                     0.135489
      25.0                     0.154642
      30.0                     0.177255
      35.0                     0.134197
      40.0                     0.142802
      45.0                     0.099144
      50.0                     0.081554
      55.0                     0.035186
      56.0                     0.032498
      60.0                     0.179690
      65.0                     0.234025
      70.0                     0.149851

Bottom line:
- `raw` remains the safest primary series.
- `eps_lr_rr` is structurally mis-matched.
- `alpha/beta`-style kernels improve the correction and support the user's physical decomposition.
- but with the current data and first-order model, they are still best treated as exploratory/supplementary rather than headline metrics.
