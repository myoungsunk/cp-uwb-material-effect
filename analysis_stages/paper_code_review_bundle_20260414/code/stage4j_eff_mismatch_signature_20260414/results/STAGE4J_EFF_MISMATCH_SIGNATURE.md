# Stage 4j: EFF Mismatch Signature

## 1. Phase drift fit
 theta_min_deg  theta_max_deg  slope_rad_per_cos  intercept_rad  effective_path_offset_m  effective_path_offset_mm       r2
          20.0           55.0          -0.300686       0.496975                -0.001104                 -1.103625 0.744901

Interpretation: phase_diff was fit as a linear function of cos(theta).

## 2. PEC normalization independence check
 with_gamma_x_mean_db  force1_mean_db  proxy_mean_db  force1_minus_with_gamma_x_mean_db  force1_minus_with_gamma_x_abs_max_db  force1_minus_proxy_mean_db  with_gamma_x_minus_proxy_mean_db
           -12.380431       -12.31188      -7.640882                           0.068552                              1.121008                   -4.670998                         -4.739549

Selected rows:
 theta_deg  leakage_actual_with_gamma_x_db  leakage_actual_force1_db   proxy_db  delta_db_with_gamma_x_vs_force1  delta_db_force1_vs_proxy
      10.0                      -12.623598                -11.502590  -4.097665                         1.121008                 -7.404925
      15.0                      -11.499243                -10.747795  -4.745421                         0.751449                 -6.002373
      20.0                      -10.639312                -11.467904  -5.377652                        -0.828592                 -6.090252
      25.0                      -10.619556                -10.608248  -5.982318                         0.011308                 -4.625930
      30.0                      -10.627860                -10.025006  -6.554669                         0.602853                 -3.470337
      35.0                      -10.416578                -11.005158  -7.097074                        -0.588580                 -3.908084
      40.0                      -11.333710                -10.999564  -7.619168                         0.334147                 -3.380396
      45.0                      -11.290487                -11.596419  -8.137019                        -0.305932                 -3.459399
      50.0                      -12.629356                -12.396120  -8.670861                         0.233236                 -3.725259
      55.0                      -12.879222                -13.201565  -9.242046                        -0.322344                 -3.959520
      60.0                      -14.481984                -14.325254  -9.870434                         0.156730                 -4.454820
      65.0                      -15.656190                -15.688527 -10.573067                        -0.032337                 -5.115460
      70.0                      -16.248512                -16.490287 -11.364073                        -0.241775                 -5.126214

## 3. Material dependence check
   group  n  residual_to_correction_ratio_mean  overcorr_db_mean  corr_ratio_vs_overcorr  slope_overcorr_per_unit_ratio
 overall 29                           0.546536          1.530547                0.284937                       1.559022
concrete 10                           0.492334          3.409548                0.579859                       4.760589
   glass 11                           0.602985          0.210413                0.462730                       0.513303
    wood  8                           0.536672          0.996981                0.290945                       1.342119

Worst rows:
material  theta_deg  Gamma_X_mag  eps_mag  gamma_hat_x_cp_sys_mag  corr_scale  residual_to_correction_ratio  gamma_hat_c_cp_eff_mag  eff_vs_ideal_db  overcorr_db
concrete       40.0     0.089012 0.415950                0.419568    0.174520                      0.510041                0.033411        -8.511229     8.511229
concrete       35.0     0.071869 0.441719                0.376917    0.166492                      0.431668                0.027989        -8.191032     8.191032
concrete       45.0     0.139044 0.391876                0.389926    0.152803                      0.909957                0.054971        -8.060396     8.060396
    wood       35.0     0.067121 0.441719                0.201779    0.089129                      0.753069                0.030234        -6.927326     6.927326
concrete       50.0     0.167934 0.368517                0.408636    0.150589                      1.115180                0.083208        -6.099476     6.099476
concrete       55.0     0.175456 0.345062                0.376031    0.129754                      1.352220                0.120921        -3.233349     3.233349
   glass       55.0     0.217662 0.345062                0.426009    0.147000                      1.480701                0.166746        -2.314543     2.314543
    wood       45.0     0.120057 0.391876                0.193731    0.075918                      1.581400                0.106405        -1.048519     1.048519
concrete       30.0     0.036701 0.470183                0.428809    0.201619                      0.182032                0.043992         1.573827     0.000000
concrete       10.0     0.004929 0.623903                0.445008    0.277641                      0.017753                0.180820        31.289789     0.000000
concrete       25.0     0.035062 0.502209                0.397500    0.199628                      0.175635                0.065640         5.446766     0.000000
concrete       20.0     0.029821 0.538415                0.358167    0.192842                      0.154642                0.078581         8.415792     0.000000