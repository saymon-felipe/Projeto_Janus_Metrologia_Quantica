# Mapa de Reorganização — Importação `teste janus` → Projeto_Janus_Metrologia_Quantica

Data da reorganização: 2026-05-15T16:04:58.764730+00:00

## Objetivo

Integrar os novos testes da pasta `teste janus` no repositório principal, separando scripts, dados brutos, resultados validados e documentação de reprodutibilidade.

## Nova organização adicionada

### Scripts

- `01_Scripts/E_Auditoria_UltraBlindada_V9/` — auditoria REAL/NULO/PHAN, massa bruta vs pós-seleção, validação por permutação.
- `01_Scripts/F_Telegrafia_Janus_V9_RAW_POST/` — transmissor/analisador V9 para mensagem `JANUS`, modo RAW e modo `POST_Q1_1`.
- `01_Scripts/G_Telegrafia_Janus_V91_SoftDecoder/` — decoder V9.1 com decisão vetorial e codebook Hamming(9,5).

### Dados brutos novos

- `02_Datasets_Brutos/Auditoria_UltraBlindada/IBM_Fez/FEZ_ULTRABLIND_001/`
- `02_Datasets_Brutos/Auditoria_UltraBlindada/IBM_Kingston/JANUS_ibm_kingston_20260514_145608/`
- `02_Datasets_Brutos/telegrafia/V9_RAW_POST/IBM_Fez/FEZ_JANUS_V9_SCOUT_512/`
- `02_Datasets_Brutos/telegrafia/V9_RAW_POST/IBM_Kingston/FEZ_JANUS_V9_DEF_512x2/`
- `02_Datasets_Brutos/telegrafia/V91_SoftDecoder/IBM_Marrakesh/KINGSTON_JANUS_V91_512x3/`

### Resultados validados novos

- `03_Resultados_Validados/Auditoria_UltraBlindada/`
- `03_Resultados_Validados/telegrafia/V9_RAW_POST/`
- `03_Resultados_Validados/telegrafia/V91_SoftDecoder/`

## Observações importantes

1. A pasta original `teste janus/imb_kingston` continha erro de digitação no nome do backend. Ela foi normalizada para `IBM_Kingston`.
2. O experimento `KINGSTON_JANUS_V91_512x3` tem tag/pasta dizendo `KINGSTON`, mas o manifesto e os arquivos indicam backend real `ibm_marrakesh`. Por isso foi arquivado em `IBM_Marrakesh`, preservando o run tag original.
3. O arquivo derivado `analysis_input_merged.csv` não foi incluído; ele pode ser regenerado pelos scripts de análise e pode ultrapassar vários GB.
4. Arquivos `.env` foram removidos do pacote reorganizado por segurança. Use `.env.example` para configurar `IBM_QUANTUM_TOKEN` localmente.

## Arquivo de mapeamento completo

Veja `05_Documentacao_Reprodutibilidade/MANIFEST_REORGANIZACAO.json`.
