# JANUS V9 — Relatório RAW vs Pós-Seleção

Mensagem esperada: **JANUS**
Linhas analisadas: **25088**
Feature mode: `full`
Window ML: `8`
Permutation tests: `0`

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
| dataset   | mode      |   bit_sent |     n |   consenso_mean |   espiao_1_mean |   espiao_2_mean |   espiao_3_mean |   q1_rate |   q0_rate |
|:----------|:----------|-----------:|------:|----------------:|----------------:|----------------:|----------------:|----------:|----------:|
| REAL      | RAW       |          0 | 13312 |       0.128155  |       0.0531851 |       0.0298978 |       0.0450721 |  0.462064 |  0.483098 |
| REAL      | RAW       |          1 | 11776 |       0.0872962 |       0.0306556 |       0.023947  |       0.0326936 |  0.504586 |  0.494141 |
| REAL      | POST_Q1_1 |          0 |  6151 |       0.183385  |       0.0733214 |       0.0448708 |       0.0651927 |  1        |  0.904243 |
| REAL      | POST_Q1_1 |          1 |  5942 |       0.0876809 |       0.0314709 |       0.0237294 |       0.0324806 |  1        |  0.435207 |

## Decodificação de mensagem — agregada
| dataset   | mode      | decoded_message   | expected_message   |   payload_bit_accuracy |   char_accuracy |   hamming_corrected_count | status   |
|:----------|:----------|:------------------|:-------------------|-----------------------:|----------------:|--------------------------:|:---------|
| REAL      | RAW       | NONUS             | JANUS              |               0.822222 |             0.6 |                         5 | ok       |
| REAL      | POST_Q1_1 | JANUS             | JANUS              |               0.955556 |             1   |                         2 | ok       |

## Decodificação por ciclo
| dataset   | mode      |   cycle | decoded_message   |   payload_bit_accuracy |   char_accuracy |   hamming_corrected_count | status   |
|:----------|:----------|--------:|:------------------|-----------------------:|----------------:|--------------------------:|:---------|
| REAL      | RAW       |       0 | NONUS             |               0.822222 |             0.6 |                         5 | ok       |
| REAL      | POST_Q1_1 |       0 | JANUS             |               0.955556 |             1   |                         2 | ok       |

## Métricas ML por janelas — somente espiões
| dataset   | mode      | model   |   n_windows |   n_sequences |   accuracy |   balanced_accuracy |      auc |   perm_p_grouped |   cm_tn |   cm_fp |   cm_fn |   cm_tp | reason   |
|:----------|:----------|:--------|------------:|--------------:|-----------:|--------------------:|---------:|-----------------:|--------:|--------:|--------:|--------:|:---------|
| REAL      | RAW       | logreg  |        2880 |            45 |   0.498958 |            0.497117 | 0.512725 |              nan |     806 |     730 |     713 |     631 | ok       |
| REAL      | POST_Q1_1 | logreg  |        1367 |            45 |   0.629846 |            0.630392 | 0.664519 |              nan |     418 |     278 |     228 |     443 | ok       |

## Controle SHAM / pareidolia de mensagem
| dataset   | mode      |   sham_trials |   exact_message_hits |   exact_message_rate |   best_char_accuracy | best_decoded_message   |
|:----------|:----------|--------------:|---------------------:|---------------------:|---------------------:|:-----------------------|
| REAL      | RAW       |           200 |                    0 |                    0 |                  0.6 | NONUS                  |
| REAL      | POST_Q1_1 |           200 |                  200 |                    1 |                  1   | JANUS                  |

## Interpretação operacional
- `POST_Q1_1`: decodificação com pós-seleção futura, compatível com o protocolo V8.
- `RAW`: tentativa de recuperação macroscópica sem pós-seleção; este é o teste relevante para vazamento operacional/no-signal.
- `NULO`: remove o emaranhamento `CX(0,1)`; deve falhar se o canal depender da ponte EPR.
- `PHAN_STRICT_POSTHOC`: mantém circuito emaranhado sem marreta; deve falhar se a mensagem depender da intervenção ativa e não de pareidolia/drift.

## Arquivos gerados
- `janus_v9_analysis_fez_janus_scout\shot_level_bit_summary.csv`
- `janus_v9_analysis_fez_janus_scout\decode_results.csv`
- `janus_v9_analysis_fez_janus_scout\cycle_decode_results.csv`
- `janus_v9_analysis_fez_janus_scout\block_features.csv`
- `janus_v9_analysis_fez_janus_scout\decode_distances.csv`
- `janus_v9_analysis_fez_janus_scout\model_metrics.csv`
- `janus_v9_analysis_fez_janus_scout\sham_message_results.csv`