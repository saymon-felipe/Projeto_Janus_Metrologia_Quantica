# CHANGELOG — V9 e V9.1

## V9 — Telegrafia RAW vs Pós-Seleção

- Adicionada mensagem curta `JANUS` usando alfabeto Baudot customizado.
- Adicionados controles `NULO` e `PHAN_STRICT_POSTHOC` no mesmo protocolo de telegrafia.
- Adicionado modo `RAW`, sem pós-seleção, para auditoria operacional de não-comunicação.
- Adicionado modo `POST_Q1_1`, compatível com o protocolo V8.
- Adicionados relatórios por ciclo, métricas ML e testes SHAM.

## V9.1 — Soft Decoder

- Adicionado decoder vetorial que usa os três espiões separadamente.
- Adicionado codebook Hamming(9,5) para decisão soft por caractere.
- Adicionado header estendido de 16 bits em rodada experimental.
- Resultado V9.1 preserva sucesso pós-selecionado, mas não estabiliza recuperação RAW em 100% na rodada importada.

## Segurança

- `.env` removido do repositório reorganizado.
- `.env.example` adicionado.
