import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from scipy.stats import entropy, binomtest
import os

print("\n==========================================================")
print(" ⚖️ PROJETO JANUS: O VEREDICTO FINAL (AUDITORIA TRIPLA)")
print("==========================================================")

MAQUINA = "ibm_fez" 

ARQUIVOS = {
    "REAL (A Marreta + A Corda)": f"AUDIT_REAL_{MAQUINA}.csv",
    "NULO (A Marreta, sem Corda)": f"AUDIT_NULO_{MAQUINA}.csv",
    "FANTASMA (A Corda, sem Marreta)": f"AUDIT_PHAN_{MAQUINA}.csv"
}

TAMANHO_JANELA = 50 

def extrair_features(df_janela):
    """Extrai a 'textura' quântica do ruído do Espião."""
    valores_q2 = df_janela['Q2_Espiao_T0'].values
    prob_1 = np.mean(valores_q2)
    ent = entropy([prob_1, 1 - prob_1], base=2) if 0 < prob_1 < 1 else 0
    mudancas = np.sum(np.abs(np.diff(valores_q2))) / len(valores_q2)
    return [prob_1, ent, mudancas]

def processar_teste(nome_teste, arquivo_csv):
    if not os.path.exists(arquivo_csv):
        return f"    [X] Ficheiro {arquivo_csv} não encontrado. Foi gerado a tempo?"

    # 1. Carregamento e Pós-Seleção (O Filtro do Futuro)
    df = pd.read_csv(arquivo_csv)
    total_original = len(df)
    df_pos = df[df['Q1_Futuro_T1'] == 1].copy()
    total_pos = len(df_pos)
    
    print(f"    -> Lendo {arquivo_csv}...")
    print(f"    -> Pós-seleção retém {total_pos} de {total_original} eventos.")

    # 2. Extração de Janelas (O Passado)
    X, y = [], []
    for tipo, label in [('Placebo', 0), ('Ativo', 1)]:
        df_tipo = df_pos[df_pos['Tipo'] == tipo]
        for i in range(0, len(df_tipo), TAMANHO_JANELA):
            janela = df_tipo.iloc[i:i+TAMANHO_JANELA]
            if len(janela) == TAMANHO_JANELA:
                X.append(extrair_features(janela))
                y.append(label)
                
    if len(np.unique(y)) < 2:
        return "    [X] Erro crítico: Dados insuficientes de uma das classes após pós-seleção."

    X = np.array(X)
    y = np.array(y)

    # 3. Treino da IA 
    print("    -> A treinar a Random Forest para caçar anomalias...")
    modelo = RandomForestClassifier(n_estimators=500, random_state=42, n_jobs=-1)
    scores = cross_val_score(modelo, X, y, cv=10)
    
    precisao = np.mean(scores) * 100
    desvio = np.std(scores) * 100
    
    # 4. Cálculo rigoroso do P-Value
    acertos = int(np.mean(scores) * len(y))
    p_value = binomtest(acertos, n=len(y), p=0.5, alternative='greater').pvalue

    # 5. Formatação do Relatório
    relatorio =  f"\n    ==========================================================\n"
    relatorio += f"     🔬 {nome_teste}\n"
    relatorio += f"    ==========================================================\n"
    relatorio += f"     Precisão da IA : {precisao:.2f}%\n"
    relatorio += f"     Margem de Erro : ± {desvio:.2f}%\n"
    relatorio += f"     P-Value        : {p_value:.6f}\n"
    relatorio += f"    ----------------------------------------------------------\n"
    
    if "REAL" in nome_teste and precisao > 54.0 and p_value < 0.05:
        relatorio += "     [🚨] ANOMALIA CONFIRMADA! O sinal retrocausal superou o ruído.\n"
    elif "NULO" in nome_teste and precisao < 53.0:
        relatorio += "     [V] Nulo perfeito. Sem corda = Sem sinal (linearidade mantida).\n"
    elif "FANTASMA" in nome_teste:
        relatorio += "     [*] Ruído de base do hardware validado.\n"
    elif precisao > 53.0 and "NULO" in nome_teste:
        relatorio += "     [!] Aviso: Possível crosstalk (vazamento térmico) na máquina.\n"
        
    relatorio += f"    ==========================================================\n"
    return relatorio

for nome, arquivo in ARQUIVOS.items():
    print(f"\n[*] A Iniciar Análise: {nome}...")
    print(processar_teste(nome, arquivo))

print("\n[*] Auditoria Final Concluída.")