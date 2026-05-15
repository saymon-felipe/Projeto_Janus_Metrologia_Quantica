# JANUS V9.1 — RAW Soft Decoder

Mensagem esperada: **JANUS**
Linhas analisadas: **281088**
Header: `0101010101010101`
Feature mode: `v91`
Distance power: `2.0`

## Sequência codificada
```json
{
  "message": "JANUS",
  "alphabet": " ABCDEFGHIJKLMNOPQRSTUVWXYZ",
  "header": "0101010101010101",
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
  "sequence_bits": "0101010101010101010011000000011001111010000110101010101101011",
  "num_header_bits": 16,
  "num_payload_bits": 45,
  "num_sequence_bits": 61
}
```

## Resumo shot-level
| dataset             | mode      |   bit_sent |     n |   consenso_mean |   espiao_1_mean |   espiao_2_mean |   espiao_3_mean |   e1_minus_e2 |   e2_minus_e3 |   q1_rate |   q0_rate |
|:--------------------|:----------|-----------:|------:|----------------:|----------------:|----------------:|----------------:|--------------:|--------------:|----------:|----------:|
| NULO                | RAW       |          0 | 49152 |       0.0963745 |       0.0349121 |       0.0360107 |       0.0254517 |  -0.00109863  |   0.0105591   |  0.466105 |  0.456645 |
| NULO                | RAW       |          1 | 44544 |       0.0953888 |       0.0350889 |       0.035044  |       0.0252559 |   4.48994e-05 |   0.00978807  |  0.594962 |  0.454854 |
| NULO                | POST_Q1_1 |          0 | 22910 |       0.0952423 |       0.0356613 |       0.0334352 |       0.0261458 |   0.0022261   |   0.00728939  |  1        |  0.451157 |
| NULO                | POST_Q1_1 |          1 | 26502 |       0.095955  |       0.0353558 |       0.0353181 |       0.0252811 |   3.7733e-05  |   0.010037    |  1        |  0.454607 |
| PHAN_STRICT_POSTHOC | RAW       |          0 | 49152 |       0.107992  |       0.0369466 |       0.0376994 |       0.0333455 |  -0.000752767 |   0.00435384  |  0.488485 |  0.484212 |
| PHAN_STRICT_POSTHOC | RAW       |          1 | 44544 |       0.109375  |       0.0382094 |       0.0370645 |       0.0341011 |   0.00114494  |   0.00296336  |  0.488281 |  0.483993 |
| PHAN_STRICT_POSTHOC | POST_Q1_1 |          0 | 24010 |       0.1611    |       0.0576426 |       0.0540192 |       0.0494377 |   0.00362349  |   0.00458142  |  1        |  0.908913 |
| PHAN_STRICT_POSTHOC | POST_Q1_1 |          1 | 21750 |       0.162851  |       0.0590345 |       0.0522759 |       0.0515402 |   0.00675862  |   0.000735632 |  1        |  0.90823  |
| REAL                | RAW       |          0 | 49152 |       0.110087  |       0.0369263 |       0.0384521 |       0.0347087 |  -0.00152588  |   0.00374349  |  0.488159 |  0.483785 |
| REAL                | RAW       |          1 | 44544 |       0.103605  |       0.0318112 |       0.0371543 |       0.0346399 |  -0.00534303  |   0.00251437  |  0.501392 |  0.490751 |
| REAL                | POST_Q1_1 |          0 | 23994 |       0.162416  |       0.0561807 |       0.0556806 |       0.0505543 |   0.000500125 |   0.00512628  |  1        |  0.903393 |
| REAL                | POST_Q1_1 |          1 | 22334 |       0.106833  |       0.0338497 |       0.0377899 |       0.035193  |  -0.00394018  |   0.00259694  |  1        |  0.49006  |

## Decodificação agregada
| dataset             | mode      | cycle     | decoder              | decoded_message   | expected_message   |   payload_bit_accuracy |   char_accuracy |   hamming_corrected_count | status   |
|:--------------------|:----------|:----------|:---------------------|:------------------|:-------------------|-----------------------:|----------------:|--------------------------:|:---------|
| NULO                | RAW       | aggregate | hard_vector          | D BH              | JANUS              |               0.444444 |             0   |                         4 | ok       |
| NULO                | RAW       | aggregate | soft_vector_codebook | DJAH              | JANUS              |               0.355556 |             0   |                       nan | ok       |
| NULO                | POST_Q1_1 | aggregate | hard_vector          | JD ZQ             | JANUS              |               0.511111 |             0.2 |                         4 | ok       |
| NULO                | POST_Q1_1 | aggregate | soft_vector_codebook | JHAZQ             | JANUS              |               0.511111 |             0.2 |                       nan | ok       |
| PHAN_STRICT_POSTHOC | RAW       | aggregate | hard_vector          | ?QYLV             | JANUS              |               0.4      |             0   |                         4 | ok       |
| PHAN_STRICT_POSTHOC | RAW       | aggregate | soft_vector_codebook | XQYLV             | JANUS              |               0.422222 |             0   |                       nan | ok       |
| PHAN_STRICT_POSTHOC | POST_Q1_1 | aggregate | hard_vector          | Q?ELN             | JANUS              |               0.4      |             0   |                         4 | ok       |
| PHAN_STRICT_POSTHOC | POST_Q1_1 | aggregate | soft_vector_codebook | YZEON             | JANUS              |               0.4      |             0   |                       nan | ok       |
| REAL                | RAW       | aggregate | hard_vector          | ?LH?S             | JANUS              |               0.755556 |             0.2 |                         3 | ok       |
| REAL                | RAW       | aggregate | soft_vector_codebook | QPHUS             | JANUS              |               0.733333 |             0.4 |                       nan | ok       |
| REAL                | POST_Q1_1 | aggregate | hard_vector          | JANUS             | JANUS              |               1        |             1   |                         0 | ok       |
| REAL                | POST_Q1_1 | aggregate | soft_vector_codebook | JANUS             | JANUS              |               1        |             1   |                       nan | ok       |

## Decodificação por ciclo
| dataset             | mode      |   cycle | decoder              | decoded_message   | expected_message   |   payload_bit_accuracy |   char_accuracy |   hamming_corrected_count | status   |
|:--------------------|:----------|--------:|:---------------------|:------------------|:-------------------|-----------------------:|----------------:|--------------------------:|:---------|
| NULO                | RAW       |       0 | hard_vector          | AYGPV             | JANUS              |               0.466667 |             0   |                         4 | ok       |
| NULO                | RAW       |       0 | soft_vector_codebook | APGPD             | JANUS              |               0.4      |             0   |                       nan | ok       |
| NULO                | RAW       |       1 | hard_vector          | Z??V?             | JANUS              |               0.511111 |             0   |                         2 | ok       |
| NULO                | RAW       |       1 | soft_vector_codebook | ZZZVL             | JANUS              |               0.444444 |             0   |                       nan | ok       |
| NULO                | RAW       |       2 | hard_vector          | NHDZ              | JANUS              |               0.466667 |             0   |                         5 | ok       |
| NULO                | RAW       |       2 | soft_vector_codebook | RNDH              | JANUS              |               0.422222 |             0   |                       nan | ok       |
| NULO                | POST_Q1_1 |       0 | hard_vector          | QPKY?             | JANUS              |               0.444444 |             0   |                         2 | ok       |
| NULO                | POST_Q1_1 |       0 | soft_vector_codebook | M KPL             | JANUS              |               0.4      |             0   |                       nan | ok       |
| NULO                | POST_Q1_1 |       1 | hard_vector          | JDAXG             | JANUS              |               0.511111 |             0.2 |                         3 | ok       |
| NULO                | POST_Q1_1 |       1 | soft_vector_codebook | JDALW             | JANUS              |               0.488889 |             0.2 |                       nan | ok       |
| NULO                | POST_Q1_1 |       2 | hard_vector          | DHE?U             | JANUS              |               0.511111 |             0   |                         3 | ok       |
| NULO                | POST_Q1_1 |       2 | soft_vector_codebook | DHDOU             | JANUS              |               0.6      |             0   |                       nan | ok       |
| PHAN_STRICT_POSTHOC | RAW       |       0 | hard_vector          | ?CBS              | JANUS              |               0.533333 |             0.2 |                         3 | ok       |
| PHAN_STRICT_POSTHOC | RAW       |       0 | soft_vector_codebook | XQ Z              | JANUS              |               0.4      |             0   |                       nan | ok       |
| PHAN_STRICT_POSTHOC | RAW       |       1 | hard_vector          | RMQMP             | JANUS              |               0.422222 |             0   |                         5 | ok       |
| PHAN_STRICT_POSTHOC | RAW       |       1 | soft_vector_codebook | RJAM              | JANUS              |               0.4      |             0   |                       nan | ok       |
| PHAN_STRICT_POSTHOC | RAW       |       2 | hard_vector          | MSX?D             | JANUS              |               0.377778 |             0   |                         3 | ok       |
| PHAN_STRICT_POSTHOC | RAW       |       2 | soft_vector_codebook | MSXKD             | JANUS              |               0.444444 |             0   |                       nan | ok       |
| PHAN_STRICT_POSTHOC | POST_Q1_1 |       0 | hard_vector          | P YD              | JANUS              |               0.466667 |             0   |                         1 | ok       |
| PHAN_STRICT_POSTHOC | POST_Q1_1 |       0 | soft_vector_codebook | QRCC              | JANUS              |               0.422222 |             0   |                       nan | ok       |
| PHAN_STRICT_POSTHOC | POST_Q1_1 |       1 | hard_vector          | RJQEV             | JANUS              |               0.422222 |             0   |                         5 | ok       |
| PHAN_STRICT_POSTHOC | POST_Q1_1 |       1 | soft_vector_codebook | RZAEV             | JANUS              |               0.444444 |             0   |                       nan | ok       |
| PHAN_STRICT_POSTHOC | POST_Q1_1 |       2 | hard_vector          | OSQND             | JANUS              |               0.266667 |             0   |                         4 | ok       |
| PHAN_STRICT_POSTHOC | POST_Q1_1 |       2 | soft_vector_codebook | ESYOX             | JANUS              |               0.4      |             0   |                       nan | ok       |
| REAL                | RAW       |       0 | hard_vector          | TKVRE             | JANUS              |               0.555556 |             0   |                         3 | ok       |
| REAL                | RAW       |       0 | soft_vector_codebook | VKVTN             | JANUS              |               0.577778 |             0   |                       nan | ok       |
| REAL                | RAW       |       1 | hard_vector          | VLH?B             | JANUS              |               0.533333 |             0   |                         5 | ok       |
| REAL                | RAW       |       1 | soft_vector_codebook | VLHYB             | JANUS              |               0.577778 |             0   |                       nan | ok       |
| REAL                | RAW       |       2 | hard_vector          | ZTL A             | JANUS              |               0.622222 |             0   |                         4 | ok       |
| REAL                | RAW       |       2 | soft_vector_codebook | XT  S             | JANUS              |               0.622222 |             0.2 |                       nan | ok       |
| REAL                | POST_Q1_1 |       0 | hard_vector          | RANUG             | JANUS              |               0.822222 |             0.6 |                         3 | ok       |
| REAL                | POST_Q1_1 |       0 | soft_vector_codebook | JANUS             | JANUS              |               1        |             1   |                       nan | ok       |
| REAL                | POST_Q1_1 |       1 | hard_vector          | JANVG             | JANUS              |               0.822222 |             0.6 |                         1 | ok       |
| REAL                | POST_Q1_1 |       1 | soft_vector_codebook | JANUS             | JANUS              |               1        |             1   |                       nan | ok       |
| REAL                | POST_Q1_1 |       2 | hard_vector          | YANRS             | JANUS              |               0.844444 |             0.6 |                         2 | ok       |
| REAL                | POST_Q1_1 |       2 | soft_vector_codebook | QANRS             | JANUS              |               0.8      |             0.6 |                       nan | ok       |

## Hit summary
| dataset             | mode      | decoder              |   n_decodes |   exact_message_hits |   best_char_accuracy | best_decoded_message   |
|:--------------------|:----------|:---------------------|------------:|---------------------:|---------------------:|:-----------------------|
| NULO                | POST_Q1_1 | hard_vector          |           4 |                    0 |                  0.2 | JD ZQ                  |
| NULO                | POST_Q1_1 | soft_vector_codebook |           4 |                    0 |                  0.2 | JHAZQ                  |
| NULO                | RAW       | hard_vector          |           4 |                    0 |                  0   | D BH                   |
| NULO                | RAW       | soft_vector_codebook |           4 |                    0 |                  0   | DJAH                   |
| PHAN_STRICT_POSTHOC | POST_Q1_1 | hard_vector          |           4 |                    0 |                  0   | Q?ELN                  |
| PHAN_STRICT_POSTHOC | POST_Q1_1 | soft_vector_codebook |           4 |                    0 |                  0   | YZEON                  |
| PHAN_STRICT_POSTHOC | RAW       | hard_vector          |           4 |                    0 |                  0.2 | ?CBS                   |
| PHAN_STRICT_POSTHOC | RAW       | soft_vector_codebook |           4 |                    0 |                  0   | XQYLV                  |
| REAL                | POST_Q1_1 | hard_vector          |           4 |                    1 |                  1   | JANUS                  |
| REAL                | POST_Q1_1 | soft_vector_codebook |           4 |                    3 |                  1   | JANUS                  |
| REAL                | RAW       | hard_vector          |           4 |                    0 |                  0.2 | ?LH?S                  |
| REAL                | RAW       | soft_vector_codebook |           4 |                    0 |                  0.4 | QPHUS                  |

## Observação metodológica
- `RAW` não usa `q1_futuro`, `q0_passado` nem pós-seleção.
- `POST_Q1_1` usa `q1_futuro == 1` apenas como filtro, nunca como feature.
- O decoder `soft_vector_codebook` testa todos os codewords Hamming(9,5) válidos do alfabeto Janus e escolhe o menor custo vetorial.
- Para alegação forte, o sucesso deve aparecer no REAL e falhar em NULO/PHAN_STRICT.