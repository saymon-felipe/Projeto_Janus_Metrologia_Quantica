# JANUS V9 — Relatório RAW vs Pós-Seleção

Mensagem esperada: **JANUS**
Linhas analisadas: **150528**
Feature mode: `full`
Window ML: `8`
Permutation tests: `1000`

## Sequência codificada
```json
{
  "message": "JANUS",
  "alphabet": " ABCDEFGHIJKLMNOPQRSTUVWXYZ",
  "header": "0101",
  "bits_5": [
    "01010",
    "00001",
    "01110",
    "10101",
    "10011"
  ],
  "hamming_9_5_blocks": [
    "010010100",
    "100000011",
    "000111100",
    "001101011",
    "101100111"
  ],
  "payload_interleaved": "010011000000011001111010000110101010101101011",
  "sequence_bits": "0101010011000000011001111010000110101010101101011",
  "num_sequence_bits": 49,
  "num_payload_bits": 45
}
```

## Resumo shot-level por bit
| dataset             | mode      |   bit_sent |     n |   consenso_mean |   espiao_1_mean |   espiao_2_mean |   espiao_3_mean |   q1_rate |   q0_rate |
|:--------------------|:----------|-----------:|------:|----------------:|----------------:|----------------:|----------------:|----------:|----------:|
| NULO                | RAW       |          0 | 26624 |       0.0664062 |       0.0237755 |       0.0247521 |       0.0178786 |  0.48723  |  0.442495 |
| NULO                | RAW       |          1 | 23552 |       0.0653023 |       0.0249236 |       0.0220788 |       0.0182999 |  0.558721 |  0.442977 |
| NULO                | POST_Q1_1 |          0 | 12972 |       0.063984  |       0.0232038 |       0.0244372 |       0.0163429 |  1        |  0.442492 |
| NULO                | POST_Q1_1 |          1 | 13159 |       0.0674063 |       0.0256858 |       0.0231781 |       0.0185424 |  1        |  0.436507 |
| PHAN_STRICT_POSTHOC | RAW       |          0 | 26624 |       0.0828951 |       0.0329778 |       0.0203576 |       0.0295598 |  0.475248 |  0.489934 |
| PHAN_STRICT_POSTHOC | RAW       |          1 | 23552 |       0.0798234 |       0.0324813 |       0.0188094 |       0.0285326 |  0.469217 |  0.483781 |
| PHAN_STRICT_POSTHOC | POST_Q1_1 |          0 | 12653 |       0.138149  |       0.0496325 |       0.0383308 |       0.0501857 |  1        |  0.921995 |
| PHAN_STRICT_POSTHOC | POST_Q1_1 |          1 | 11051 |       0.135101  |       0.0512171 |       0.0359244 |       0.0479595 |  1        |  0.915845 |
| REAL                | RAW       |          0 | 26624 |       0.0810922 |       0.0341421 |       0.0181415 |       0.0288086 |  0.466572 |  0.479605 |
| REAL                | RAW       |          1 | 23552 |       0.081267  |       0.0211447 |       0.0361753 |       0.023947  |  0.50518  |  0.471934 |
| REAL                | POST_Q1_1 |          0 | 12422 |       0.135244  |       0.051924  |       0.0346965 |       0.0486234 |  1        |  0.916278 |
| REAL                | POST_Q1_1 |          1 | 11898 |       0.0800134 |       0.0204236 |       0.0378215 |       0.0217684 |  1        |  0.479744 |

## Decodificação de mensagem — agregada
| dataset             | mode      | decoded_message   | expected_message   |   payload_bit_accuracy |   char_accuracy |   hamming_corrected_count | status   |
|:--------------------|:----------|:------------------|:-------------------|-----------------------:|----------------:|--------------------------:|:---------|
| NULO                | RAW       | P PL              | JANUS              |               0.466667 |             0   |                         5 | ok       |
| NULO                | POST_Q1_1 | DAGPH             | JANUS              |               0.555556 |             0.2 |                         3 | ok       |
| PHAN_STRICT_POSTHOC | RAW       | ?ETWM             | JANUS              |               0.488889 |             0   |                         2 | ok       |
| PHAN_STRICT_POSTHOC | POST_Q1_1 | ?UT?G             | JANUS              |               0.466667 |             0   |                         4 | ok       |
| REAL                | RAW       | ANUS              | JANUS              |               0.911111 |             0.8 |                         3 | ok       |
| REAL                | POST_Q1_1 | JANUS             | JANUS              |               0.977778 |             1   |                         1 | ok       |

## Decodificação por ciclo
| dataset             | mode      |   cycle | decoded_message   |   payload_bit_accuracy |   char_accuracy |   hamming_corrected_count | status   |
|:--------------------|:----------|--------:|:------------------|-----------------------:|----------------:|--------------------------:|:---------|
| NULO                | RAW       |       0 | BIERA             |               0.533333 |             0   |                         4 | ok       |
| NULO                | RAW       |       1 | HBBP              |               0.466667 |             0   |                         2 | ok       |
| NULO                | POST_Q1_1 |       0 | FAFB?             |               0.488889 |             0.2 |                         2 | ok       |
| NULO                | POST_Q1_1 |       1 | B                 |               0.511111 |             0   |                         3 | ok       |
| PHAN_STRICT_POSTHOC | RAW       |       0 | ?Y?U?             |               0.555556 |             0.2 |                         5 | ok       |
| PHAN_STRICT_POSTHOC | RAW       |       1 | UMMEH             |               0.488889 |             0   |                         3 | ok       |
| PHAN_STRICT_POSTHOC | POST_Q1_1 |       0 | V??X?             |               0.422222 |             0   |                         3 | ok       |
| PHAN_STRICT_POSTHOC | POST_Q1_1 |       1 | DL?GH             |               0.511111 |             0   |                         3 | ok       |
| REAL                | RAW       |       0 | BGNEF             |               0.733333 |             0.2 |                         2 | ok       |
| REAL                | RAW       |       1 | JANUA             |               0.933333 |             0.8 |                         2 | ok       |
| REAL                | POST_Q1_1 |       0 | JANUS             |               0.955556 |             1   |                         2 | ok       |
| REAL                | POST_Q1_1 |       1 | JANUS             |               0.955556 |             1   |                         2 | ok       |

## Métricas ML por janelas — somente espiões
| dataset             | mode      | model   |   n_windows |   n_sequences |   accuracy |   balanced_accuracy |      auc |   perm_p_grouped |   cm_tn |   cm_fp |   cm_fn |   cm_tp | reason   |
|:--------------------|:----------|:--------|------------:|--------------:|-----------:|--------------------:|---------:|-----------------:|--------:|--------:|--------:|--------:|:---------|
| NULO                | RAW       | logreg  |        5760 |            45 |   0.468403 |            0.450056 | 0.395082 |      0.373626    |    2228 |     844 |    2218 |     470 | ok       |
| NULO                | POST_Q1_1 | logreg  |        2959 |            45 |   0.483609 |            0.4836   | 0.480966 |      0.163836    |     709 |     765 |     763 |     722 | ok       |
| PHAN_STRICT_POSTHOC | RAW       | logreg  |        5760 |            45 |   0.427257 |            0.414039 | 0.369764 |      0.557443    |    1881 |    1191 |    2108 |     580 | ok       |
| PHAN_STRICT_POSTHOC | POST_Q1_1 | logreg  |        2681 |            45 |   0.449832 |            0.431731 | 0.365111 |      0.461538    |     988 |     447 |    1028 |     218 | ok       |
| REAL                | RAW       | logreg  |        5760 |            45 |   0.578125 |            0.556501 | 0.527754 |      0.000999001 |    2706 |     366 |    2064 |     624 | ok       |
| REAL                | POST_Q1_1 | logreg  |        2752 |            45 |   0.630451 |            0.632871 | 0.611947 |      0.000999001 |     763 |     649 |     368 |     972 | ok       |

## Controle SHAM / pareidolia de mensagem
| dataset             | mode      |   sham_trials |   exact_message_hits |   exact_message_rate |   best_char_accuracy | best_decoded_message   |
|:--------------------|:----------|--------------:|---------------------:|---------------------:|---------------------:|:-----------------------|
| NULO                | RAW       |           200 |                    0 |                    0 |                  0   |                        |
| NULO                | POST_Q1_1 |           200 |                    0 |                    0 |                  0.2 | DAGPH                  |
| PHAN_STRICT_POSTHOC | RAW       |           200 |                    0 |                    0 |                  0   |                        |
| PHAN_STRICT_POSTHOC | POST_Q1_1 |           200 |                    0 |                    0 |                  0   |                        |
| REAL                | RAW       |           200 |                    0 |                    0 |                  0.8 | ANUS                   |
| REAL                | POST_Q1_1 |           200 |                  200 |                    1 |                  1   | JANUS                  |

## Interpretação operacional
- `POST_Q1_1`: decodificação com pós-seleção futura, compatível com o protocolo V8.
- `RAW`: tentativa de recuperação macroscópica sem pós-seleção; este é o teste relevante para vazamento operacional/no-signal.
- `NULO`: remove o emaranhamento `CX(0,1)`; deve falhar se o canal depender da ponte EPR.
- `PHAN_STRICT_POSTHOC`: mantém circuito emaranhado sem marreta; deve falhar se a mensagem depender da intervenção ativa e não de pareidolia/drift.

## Arquivos gerados
- `janus_v9_analysis_kingston_janus_def_512x2\shot_level_bit_summary.csv`
- `janus_v9_analysis_kingston_janus_def_512x2\decode_results.csv`
- `janus_v9_analysis_kingston_janus_def_512x2\cycle_decode_results.csv`
- `janus_v9_analysis_kingston_janus_def_512x2\block_features.csv`
- `janus_v9_analysis_kingston_janus_def_512x2\decode_distances.csv`
- `janus_v9_analysis_kingston_janus_def_512x2\model_metrics.csv`
- `janus_v9_analysis_kingston_janus_def_512x2\sham_message_results.csv`