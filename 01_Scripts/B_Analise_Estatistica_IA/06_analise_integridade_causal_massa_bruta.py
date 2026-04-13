import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
import os

print("\n==========================================================")
print(" ⚖️ PROJETO JANUS: TESTE DE INTEGRIDADE CAUSAL (SEM PÓS-SELEÇÃO)")
print("==========================================================")

MAQUINA = "ibm_fez" 

ARQUIVOS = {
    "REAL (Massa Bruta)": f"AUDIT_REAL_PANOPTICO_{MAQUINA}.csv",
    "NULO (Massa Bruta)": f"AUDIT_NULO_PANOPTICO_{MAQUINA}.csv",
    "FANTASMA (Massa Bruta)": f"AUDIT_PHAN_PANOPTICO_{MAQUINA}.csv"
}

TAMANHO_JANELA = 16 

def processar_massa_bruta(nome_teste, arquivo_csv):
    if not os.path.exists(arquivo_csv):
        return f"    [X] Ficheiro {arquivo_csv} não encontrado."

    # CARREGAMENTO TOTAL (Sem filtrar Q1_Futuro_T1)
    df = pd.read_csv(arquivo_csv)
    
    print(f"    -> Lendo {arquivo_csv}...")
    print(f"    -> Analisando TODOS os {len(df)} eventos (Sem Pós-Seleção).")

    # Engenharia de Consenso (3 Espiões)
    df['Consenso'] = df['Espiao_1'] + df['Espiao_2'] + df['Espiao_3']

    X, y = [], []
    for tipo, label in [('Placebo', 0), ('Ativo', 1)]:
        df_tipo = df[df['Tipo'] == tipo]
        dados = df_tipo['Consenso'].values
        
        for i in range(0, len(dados) - TAMANHO_JANELA, TAMANHO_JANELA):
            janela = dados[i:i+TAMANHO_JANELA]
            if len(janela) == TAMANHO_JANELA:
                media = np.mean(janela)
                var = np.var(janela)
                flicker = np.sum(np.abs(np.diff(janela))) / len(janela)
                X.append([media, var, flicker])
                y.append(label)
                
    if len(X) == 0: return "    [X] Dados insuficientes."

    X = np.array(X)
    y = np.array(y)

    # Treino da IA
    modelo = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(modelo, X, y, cv=cv)
    
    precisao = np.mean(scores) * 100
    
    relatorio =  f"\n    ==========================================================\n"
    relatorio += f"     🔬 {nome_teste}\n"
    relatorio += f"    ==========================================================\n"
    relatorio += f"     Precisão da IA : {precisao:.2f}%\n"
    relatorio += f"    ----------------------------------------------------------\n"
    
    if precisao < 53.0:
        relatorio += "     [V] CAUSALIDADE PRESERVADA. Sem a chave do futuro, o sinal sumiu.\n"
    else:
        relatorio += "     [!] ANOMALIA PERSISTENTE. Possível erro sistemático no hardware.\n"
        
    relatorio += f"    ==========================================================\n"
    return relatorio

for nome, arquivo in ARQUIVOS.items():
    print(processar_massa_bruta(nome, arquivo))

print("\n[*] Teste de Integridade Concluído.")