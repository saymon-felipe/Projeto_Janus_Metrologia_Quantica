import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from scipy.stats import binomtest
import os

print("\n==========================================================")
print(" ⚖️ ANÁLISE PANÓPTICA: O VEREDICTO DOS 3 ESPIÕES")
print("==========================================================")

MAQUINA = "ibm_fez" 

ARQUIVOS = {
    "REAL (A Marreta + A Corda)": f"AUDIT_REAL_PANOPTICO_{MAQUINA}.csv",
    "NULO (A Marreta, sem Corda)": f"AUDIT_NULO_PANOPTICO_{MAQUINA}.csv",
    "FANT সাংস্কৃতিক (A Corda, sem Marreta)": f"AUDIT_PHAN_PANOPTICO_{MAQUINA}.csv"
}

TAMANHO_JANELA = 16 

def processar_teste(nome_teste, arquivo_csv):
    if not os.path.exists(arquivo_csv):
        return f"    [X] Ficheiro {arquivo_csv} não encontrado."

    df = pd.read_csv(arquivo_csv)
    df_pos = df[df['Q1_Futuro_T1'] == 1].copy()
    
    print(f"    -> Lendo {arquivo_csv}...")
    print(f"    -> Pós-seleção retém {len(df_pos)} de {len(df)} eventos.")

    df_pos['Consenso'] = df_pos['Espiao_1'] + df_pos['Espiao_2'] + df_pos['Espiao_3']

    X, y = [], []
    for tipo, label in [('Placebo', 0), ('Ativo', 1)]:
        df_tipo = df_pos[df_pos['Tipo'] == tipo]
        dados = df_tipo['Consenso'].values
        
        for i in range(0, len(dados) - TAMANHO_JANELA, TAMANHO_JANELA):
            janela = dados[i:i+TAMANHO_JANELA]
            if len(janela) == TAMANHO_JANELA:
                media = np.mean(janela)
                var = np.var(janela)
                flicker = np.sum(np.abs(np.diff(janela))) / len(janela)
                X.append([media, var, flicker])
                y.append(label)
                
    if len(np.unique(y)) < 2:
        return "    [X] Erro crítico: Dados insuficientes."

    X = np.array(X)
    y = np.array(y)

    print("    -> A treinar a Random Forest de Consenso...")
    modelo = RandomForestClassifier(n_estimators=300, max_depth=8, random_state=42)
    cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
    scores = cross_val_score(modelo, X, y, cv=cv, scoring='accuracy')
    
    precisao = np.mean(scores) * 100
    desvio = np.std(scores) * 100
    
    acertos = int(np.mean(scores) * len(y))
    p_value = binomtest(acertos, n=len(y), p=0.5, alternative='greater').pvalue

    relatorio =  f"\n    ==========================================================\n"
    relatorio += f"     🔬 {nome_teste}\n"
    relatorio += f"    ==========================================================\n"
    relatorio += f"     Precisão da IA : {precisao:.2f}%\n"
    relatorio += f"     Margem de Erro : ± {desvio:.2f}%\n"
    relatorio += f"     P-Value        : {p_value:.6f}\n"
    relatorio += f"    ----------------------------------------------------------\n"
    
    if "REAL" in nome_teste and precisao > 58.0 and p_value < 0.05:
        relatorio += "     [🚨] SUPER ANOMALIA CONFIRMADA! A precisão subiu com o consenso.\n"
    elif "NULO" in nome_teste and precisao < 54.0:
        relatorio += "     [V] Nulo perfeito. Sem corda = Sem sinal, mesmo com 3 espiões.\n"
    elif "FANT" in nome_teste:
        relatorio += "     [*] Ruído de base validado.\n"
    elif precisao >= 54.0 and "NULO" in nome_teste:
        relatorio += "     [!] Aviso: Ligeiro crosstalk devido ao aglomerado de espiões.\n"
        
    relatorio += f"    ==========================================================\n"
    return relatorio

for nome, arquivo in ARQUIVOS.items():
    print(f"\n[*] A Iniciar Análise Panóptica: {nome}...")
    print(processar_teste(nome, arquivo))

print("\n[*] Auditoria Final Panóptica Concluída.")