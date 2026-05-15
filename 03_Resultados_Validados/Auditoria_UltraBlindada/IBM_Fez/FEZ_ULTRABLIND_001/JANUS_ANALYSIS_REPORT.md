# Relatório Janus — Análise Ultra-Blindada

Arquivos analisados: 1
Linhas totais: 143360
Window: 16
Feature mode: basic
Permutation tests: 1000

## Resumo shot-level

| dataset                    | postselect   |   n_placebo |   n_ativo |   consenso_placebo_mean |   consenso_ativo_mean |   consenso_delta_ativo_minus_placebo |   espiao_1_placebo_mean |   espiao_1_ativo_mean |   espiao_1_delta_ativo_minus_placebo |   espiao_2_placebo_mean |   espiao_2_ativo_mean |   espiao_2_delta_ativo_minus_placebo |   espiao_3_placebo_mean |   espiao_3_ativo_mean |   espiao_3_delta_ativo_minus_placebo |   q0_passado_placebo_mean |   q0_passado_ativo_mean |   q0_passado_delta_ativo_minus_placebo |   q1_futuro_placebo_mean |   q1_futuro_ativo_mean |   q1_futuro_delta_ativo_minus_placebo |
|:---------------------------|:-------------|------------:|----------:|------------------------:|----------------------:|-------------------------------------:|------------------------:|----------------------:|-------------------------------------:|------------------------:|----------------------:|-------------------------------------:|------------------------:|----------------------:|-------------------------------------:|--------------------------:|------------------------:|---------------------------------------:|-------------------------:|-----------------------:|--------------------------------------:|
| NULO                       | False        |       20480 |     20480 |                0.104736 |             0.106885  |                           0.00214844 |               0.0302734 |             0.0311523 |                          0.000878906 |               0.0303711 |             0.0304687 |                          9.76562e-05 |               0.0440918 |             0.0452637 |                          0.00117188  |                  0.439063 |                0.421387 |                           -0.0176758   |                 0.477295 |               0.509521 |                            0.0322266  |
| NULO                       | True         |        9775 |     10435 |                0.107826 |             0.104744  |                          -0.00308244 |               0.0296675 |             0.0308577 |                          0.00119017  |               0.0326343 |             0.0308577 |                         -0.00177658  |               0.0455243 |             0.0430283 |                         -0.00249603  |                  0.43601  |                0.417537 |                           -0.0184731   |                 1        |               1        |                            0          |
| PHAN_LEGACY_IDENTICAL_PUBS | False        |       20480 |     20480 |                0.131836 |             0.124268  |                          -0.00756836 |               0.0571289 |             0.0527832 |                         -0.0043457   |               0.0333984 |             0.0299805 |                         -0.00341797  |               0.0413086 |             0.0415039 |                          0.000195313 |                  0.485352 |                0.494824 |                            0.00947266  |                 0.467285 |               0.474609 |                            0.00732422 |
| PHAN_LEGACY_IDENTICAL_PUBS | True         |        9570 |      9720 |                0.191536 |             0.176235  |                          -0.0153015  |               0.0830721 |             0.075     |                         -0.0080721   |               0.0493208 |             0.0435185 |                         -0.00580228  |               0.0591432 |             0.057716  |                         -0.00142711  |                  0.898537 |                0.902572 |                            0.00403492  |                 1        |               1        |                            0          |
| PHAN_STRICT_POSTHOC        | False        |       10240 |     10240 |                0.127832 |             0.125098  |                          -0.00273438 |               0.0541016 |             0.0517578 |                         -0.00234375  |               0.0311523 |             0.0302734 |                         -0.000878906 |               0.0425781 |             0.0430664 |                          0.000488281 |                  0.485254 |                0.481836 |                           -0.00341797  |                 0.463477 |               0.467285 |                            0.00380859 |
| PHAN_STRICT_POSTHOC        | True         |        4746 |      4785 |                0.17678  |             0.177847  |                           0.00106699 |               0.0754319 |             0.0718913 |                         -0.00354062  |               0.0465655 |             0.0474399 |                          0.000874388 |               0.054783  |             0.0585162 |                          0.00373322  |                  0.904973 |                0.897806 |                           -0.00716697  |                 1        |               1        |                            0          |
| REAL                       | False        |       20480 |     20480 |                0.129199 |             0.0852051 |                          -0.0439941  |               0.0524414 |             0.0306152 |                         -0.0218262   |               0.0333496 |             0.0222168 |                         -0.0111328   |               0.0434082 |             0.032373  |                         -0.0110352   |                  0.486475 |                0.485498 |                           -0.000976562 |                 0.467041 |               0.501514 |                            0.0344727  |
| REAL                       | True         |        9565 |     10271 |                0.182645 |             0.0839256 |                          -0.0987194  |               0.0730789 |             0.0305715 |                         -0.0425074   |               0.0504966 |             0.0209327 |                         -0.0295639   |               0.0590695 |             0.0324214 |                         -0.0266481   |                  0.902143 |                0.454386 |                           -0.447757    |                 1        |               1        |                            0          |


## Métricas de modelo

| dataset                    | postselect   | model              |   n_windows |   accuracy |   balanced_accuracy |      auc |   binom_p_naive |   perm_p_grouped |   cm_tn |   cm_fp |   cm_fn |   cm_tp |
|:---------------------------|:-------------|:-------------------|------------:|-----------:|--------------------:|---------:|----------------:|-----------------:|--------:|--------:|--------:|--------:|
| NULO                       | False        | RandomForest       |        2560 |   0.516016 |            0.516016 | 0.512122 |        0.05469  |       nan        |     747 |     533 |     706 |     574 |
| NULO                       | False        | LogisticRegression |        2560 |   0.494531 |            0.494531 | 0.486071 |        0.716729 |         0.681319 |     547 |     733 |     561 |     719 |
| NULO                       | True         | RandomForest       |        1258 |   0.447536 |            0.445788 | 0.424051 |        0.999913 |       nan        |     238 |     371 |     324 |     325 |
| NULO                       | True         | LogisticRegression |        1258 |   0.505564 |            0.50385  | 0.497384 |        0.356995 |         0.43956  |     274 |     335 |     287 |     362 |
| PHAN_LEGACY_IDENTICAL_PUBS | False        | RandomForest       |        2560 |   0.506641 |            0.506641 | 0.501705 |        0.257134 |       nan        |     517 |     763 |     500 |     780 |
| PHAN_LEGACY_IDENTICAL_PUBS | False        | LogisticRegression |        2560 |   0.514844 |            0.514844 | 0.510797 |        0.06912  |         0.102897 |     676 |     604 |     638 |     642 |
| PHAN_LEGACY_IDENTICAL_PUBS | True         | RandomForest       |        1201 |   0.478768 |            0.47789  | 0.474705 |        0.933273 |       nan        |     215 |     381 |     245 |     360 |
| PHAN_LEGACY_IDENTICAL_PUBS | True         | LogisticRegression |        1201 |   0.535387 |            0.535161 | 0.520825 |        0.007661 |         0.012987 |     301 |     295 |     263 |     342 |
| PHAN_STRICT_POSTHOC        | False        | RandomForest       |        1280 |   0.479687 |            0.479688 | 0.49155  |        0.930765 |       nan        |     311 |     329 |     337 |     303 |
| PHAN_STRICT_POSTHOC        | False        | LogisticRegression |        1280 |   0.509375 |            0.509375 | 0.500461 |        0.260162 |         0.312687 |     331 |     309 |     319 |     321 |
| PHAN_STRICT_POSTHOC        | True         | RandomForest       |         591 |   0.532995 |            0.533194 | 0.531499 |        0.058976 |       nan        |     192 |     103 |     173 |     123 |
| PHAN_STRICT_POSTHOC        | True         | LogisticRegression |         591 |   0.473773 |            0.473866 | 0.462511 |        0.905987 |         0.837163 |     156 |     139 |     172 |     124 |
| REAL                       | False        | RandomForest       |        2560 |   0.6      |            0.6      | 0.63453  |        0        |       nan        |     760 |     520 |     504 |     776 |
| REAL                       | False        | LogisticRegression |        2560 |   0.608594 |            0.608594 | 0.640365 |        0        |         0.000999 |     754 |     526 |     476 |     804 |
| REAL                       | True         | RandomForest       |        1236 |   0.714401 |            0.714068 | 0.788256 |        0        |       nan        |     420 |     176 |     177 |     463 |
| REAL                       | True         | LogisticRegression |        1236 |   0.706311 |            0.706659 | 0.784623 |        0        |         0.000999 |     427 |     169 |     194 |     446 |


## Flags interpretativas

- REAL pós-seleção RF: 71.44%
- NULO pós-seleção RF: 44.75%
- PHAN_STRICT pós-seleção RF: 53.30%
- [OK] PHAN_STRICT próximo de 50%: controle pós-hoc passou.
- PHAN_LEGACY pós-seleção RF: 47.88%
- [FORTE] REAL excede NULO por mais de 8 pontos percentuais.


## Arquivos gerados

- janus_analysis_fez_1000\analysis_input_merged.csv
- janus_analysis_fez_1000\shot_level_summary.csv
- janus_analysis_fez_1000\q1_rate_by_lot.csv
- janus_analysis_fez_1000\model_validation_metrics.csv