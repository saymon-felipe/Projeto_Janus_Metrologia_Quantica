# Reprodutibilidade

## Instalação

```bash
pip install -r requirements.txt
```

Configure o token IBM localmente:

```bash
cp 01_Scripts/A_Extracao_Quantica/.env.example 01_Scripts/A_Extracao_Quantica/.env
# edite o arquivo e preencha IBM_QUANTUM_TOKEN
```

## Organização dos dados

- Dados brutos ficam em `02_Datasets_Brutos/`.
- Resultados e relatórios ficam em `03_Resultados_Validados/`.
- Scripts congelados ficam em `01_Scripts/`.
- Documentação de migração e protocolo fica em `05_Documentacao_Reprodutibilidade/`.

## Arquivos grandes

Não versionar `analysis_input_merged.csv`: ele é derivado e pode ser regenerado.
