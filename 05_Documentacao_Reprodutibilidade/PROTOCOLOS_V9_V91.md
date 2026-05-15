# Protocolos adicionados — V9 / V9.1

## V9 — RAW vs Pós-Seleção

Script principal:

```bash
python 01_Scripts/F_Telegrafia_Janus_V9_RAW_POST/janus_v9_janus_message_definitivo.py extract --backend ibm_kingston --message JANUS --shots 512 --cycles 2 --include-nulo --include-phan-strict --randomize-order
```

Análise:

```bash
python 01_Scripts/F_Telegrafia_Janus_V9_RAW_POST/janus_v9_janus_message_definitivo.py analyze --input "<RAW_CSV>" --message JANUS --window 8 --n-perm 1000 --outdir <PASTA_ANALISE>
```

Objetivo: comparar `RAW` sem pós-seleção contra `POST_Q1_1`, com controles `NULO` e `PHAN_STRICT_POSTHOC`.

## V9.1 — Soft Decoder Vetorial

Script principal:

```bash
python 01_Scripts/G_Telegrafia_Janus_V91_SoftDecoder/janus_v91_soft_decoder_v2_fixed.py --input "<RAW_CSV>" --message JANUS --header 0101010101010101 --outdir <PASTA_ANALISE>
```

Objetivo: testar decodificação vetorial com Hamming(9,5) por codebook, sem usar `q1_futuro` ou `q0_passado` no modo RAW.

## Critério recomendado para alegação forte

- `REAL/POST_Q1_1` deve recuperar `JANUS`.
- `REAL/RAW` deve recuperar `JANUS` ou erro mínimo, de forma repetível por ciclo.
- `NULO/RAW` e `PHAN_STRICT/RAW` devem falhar.
- O mesmo script deve ser usado sem mudanças pós-hoc.
