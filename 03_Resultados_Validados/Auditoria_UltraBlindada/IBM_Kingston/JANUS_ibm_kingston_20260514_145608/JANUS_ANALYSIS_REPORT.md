# Relatório Janus — Análise Ultra-Blindada

Arquivos analisados: 1
Linhas totais: 143360
Window: 16
Feature mode: basic
Permutation tests: 100

## Resumo shot-level

| dataset                    | postselect   |   n_placebo |   n_ativo |   consenso_placebo_mean |   consenso_ativo_mean |   consenso_delta_ativo_minus_placebo |   espiao_1_placebo_mean |   espiao_1_ativo_mean |   espiao_1_delta_ativo_minus_placebo |   espiao_2_placebo_mean |   espiao_2_ativo_mean |   espiao_2_delta_ativo_minus_placebo |   espiao_3_placebo_mean |   espiao_3_ativo_mean |   espiao_3_delta_ativo_minus_placebo |   q0_passado_placebo_mean |   q0_passado_ativo_mean |   q0_passado_delta_ativo_minus_placebo |   q1_futuro_placebo_mean |   q1_futuro_ativo_mean |   q1_futuro_delta_ativo_minus_placebo |
|:---------------------------|:-------------|------------:|----------:|------------------------:|----------------------:|-------------------------------------:|------------------------:|----------------------:|-------------------------------------:|------------------------:|----------------------:|-------------------------------------:|------------------------:|----------------------:|-------------------------------------:|--------------------------:|------------------------:|---------------------------------------:|-------------------------:|-----------------------:|--------------------------------------:|
| NULO                       | False        |       20480 |     20480 |               0.0909668 |             0.0914062 |                          0.000439453 |               0.047168  |             0.0489258 |                           0.00175781 |               0.0210938 |             0.020166  |                         -0.000927734 |               0.0227051 |             0.0223145 |                         -0.000390625 |                  0.440674 |                0.433154 |                           -0.00751953  |                 0.475928 |               0.593896 |                           0.117969    |
| NULO                       | True         |        9747 |     12163 |               0.0886427 |             0.0897805 |                          0.00113782  |               0.0453473 |             0.0470279 |                           0.00168059 |               0.0205191 |             0.0198142 |                         -0.000704944 |               0.0227762 |             0.0229384 |                          0.000162181 |                  0.440238 |                0.432295 |                           -0.00794336  |                 1        |               1        |                           0           |
| PHAN_LEGACY_IDENTICAL_PUBS | False        |       20480 |     20480 |               0.0913574 |             0.0837891 |                         -0.00756836  |               0.045166  |             0.0396973 |                          -0.00546875 |               0.0225586 |             0.0208984 |                         -0.00166016  |               0.0236328 |             0.0231934 |                         -0.000439453 |                  0.48501  |                0.481592 |                           -0.00341797  |                 0.481396 |               0.480518 |                          -0.000878906 |
| PHAN_LEGACY_IDENTICAL_PUBS | True         |        9859 |      9841 |               0.151435  |             0.142364  |                         -0.00907166  |               0.0690739 |             0.0635098 |                          -0.00556414 |               0.0414849 |             0.0390204 |                         -0.00246451  |               0.0408764 |             0.0398334 |                         -0.00104301  |                  0.949386 |                0.948887 |                           -0.000499039 |                 1        |               1        |                           0           |
| PHAN_STRICT_POSTHOC        | False        |       10240 |     10240 |               0.0886719 |             0.0849609 |                         -0.00371094  |               0.0425781 |             0.0408203 |                          -0.00175781 |               0.0225586 |             0.0195312 |                         -0.00302734  |               0.0235352 |             0.0246094 |                          0.00107422  |                  0.482812 |                0.480469 |                           -0.00234375  |                 0.479297 |               0.477246 |                          -0.00205078  |
| PHAN_STRICT_POSTHOC        | True         |        4908 |      4887 |               0.148126  |             0.143646  |                         -0.0044791   |               0.0672372 |             0.0654798 |                          -0.00175732 |               0.0407498 |             0.0351954 |                         -0.00555438  |               0.0401385 |             0.0429711 |                          0.0028326   |                  0.955379 |                0.951299 |                           -0.00407961  |                 1        |               1        |                           0           |
| REAL                       | False        |       20480 |     20480 |               0.0896973 |             0.0768555 |                         -0.0128418   |               0.0441895 |             0.0333984 |                          -0.010791   |               0.0194336 |             0.019873  |                          0.000439453 |               0.0260742 |             0.023584  |                         -0.00249023  |                  0.487256 |                0.490967 |                            0.00371094  |                 0.482129 |               0.4854   |                           0.00327148  |
| REAL                       | True         |        9874 |      9941 |               0.145129  |             0.0739362 |                         -0.0711924   |               0.0664371 |             0.0320893 |                          -0.0343478  |               0.0352441 |             0.0185092 |                         -0.0167349   |               0.0434474 |             0.0233377 |                         -0.0201097   |                  0.955033 |                0.510914 |                           -0.444119    |                 1        |               1        |                           0           |


## Métricas de modelo

| dataset                    | postselect   | model              |   n_windows |   accuracy |   balanced_accuracy |      auc |   binom_p_naive |   perm_p_grouped |   cm_tn |   cm_fp |   cm_fn |   cm_tp |
|:---------------------------|:-------------|:-------------------|------------:|-----------:|--------------------:|---------:|----------------:|-----------------:|--------:|--------:|--------:|--------:|
| NULO                       | False        | RandomForest       |        2560 |   0.514062 |            0.514063 | 0.51524  |        0.080263 |       nan        |     854 |     426 |     818 |     462 |
| NULO                       | False        | LogisticRegression |        2560 |   0.503516 |            0.503516 | 0.499563 |        0.368442 |         0.475248 |     755 |     525 |     746 |     534 |
| NULO                       | True         | RandomForest       |        1365 |   0.481319 |            0.484614 | 0.481521 |        0.920367 |       nan        |     313 |     295 |     413 |     344 |
| NULO                       | True         | LogisticRegression |        1365 |   0.484982 |            0.488078 | 0.479129 |        0.872193 |         0.782178 |     314 |     294 |     409 |     348 |
| PHAN_LEGACY_IDENTICAL_PUBS | False        | RandomForest       |        2560 |   0.528125 |            0.528125 | 0.529695 |        0.00235  |       nan        |     758 |     522 |     686 |     594 |
| PHAN_LEGACY_IDENTICAL_PUBS | False        | LogisticRegression |        2560 |   0.527734 |            0.527734 | 0.536514 |        0.002657 |         0.009901 |     461 |     819 |     390 |     890 |
| PHAN_LEGACY_IDENTICAL_PUBS | True         | RandomForest       |        1226 |   0.508972 |            0.508958 | 0.523864 |        0.274343 |       nan        |     318 |     296 |     306 |     306 |
| PHAN_LEGACY_IDENTICAL_PUBS | True         | LogisticRegression |        1226 |   0.520392 |            0.52043  | 0.530395 |        0.080829 |         0.108911 |     305 |     309 |     279 |     333 |
| PHAN_STRICT_POSTHOC        | False        | RandomForest       |        1280 |   0.517969 |            0.517969 | 0.510107 |        0.104226 |       nan        |     250 |     390 |     227 |     413 |
| PHAN_STRICT_POSTHOC        | False        | LogisticRegression |        1280 |   0.508594 |            0.508594 | 0.508279 |        0.278621 |         0.39604  |     234 |     406 |     223 |     417 |
| PHAN_STRICT_POSTHOC        | True         | RandomForest       |         609 |   0.52381  |            0.524073 | 0.524682 |        0.128259 |       nan        |     144 |     162 |     128 |     175 |
| PHAN_STRICT_POSTHOC        | True         | LogisticRegression |         609 |   0.505747 |            0.50618  | 0.502745 |        0.403964 |         0.415842 |     128 |     178 |     123 |     180 |
| REAL                       | False        | RandomForest       |        2560 |   0.539453 |            0.539453 | 0.534909 |        3.5e-05  |       nan        |     533 |     747 |     432 |     848 |
| REAL                       | False        | LogisticRegression |        2560 |   0.540625 |            0.540625 | 0.547008 |        2.1e-05  |         0.009901 |     545 |     735 |     441 |     839 |
| REAL                       | True         | RandomForest       |        1234 |   0.67423  |            0.6742   | 0.722994 |        0        |       nan        |     409 |     206 |     196 |     423 |
| REAL                       | True         | LogisticRegression |        1234 |   0.67423  |            0.674116 | 0.715282 |        0        |         0.009901 |     393 |     222 |     180 |     439 |


## Flags interpretativas

- REAL pós-seleção RF: 67.42%
- NULO pós-seleção RF: 48.13%
- PHAN_STRICT pós-seleção RF: 52.38%
- [OK] PHAN_STRICT próximo de 50%: controle pós-hoc passou.
- PHAN_LEGACY pós-seleção RF: 50.90%
- [FORTE] REAL excede NULO por mais de 8 pontos percentuais.


## Arquivos gerados

- janus_analysis_fast\analysis_input_merged.csv
- janus_analysis_fast\shot_level_summary.csv
- janus_analysis_fast\q1_rate_by_lot.csv
- janus_analysis_fast\model_validation_metrics.csv