# janus_feature_importance_fez.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from scipy.stats import entropy
import os

TAMANHO_JANELA = 50

def extrair_features(valores_q2):
    prob_1 = np.mean(valores_q2)
    ent = entropy([prob_1, 1 - prob_1], base=2) if 0 < prob_1 < 1 else 0
    mudancas = np.sum(np.abs(np.diff(valores_q2))) / len(valores_q2)
    return [prob_1, ent, mudancas]

def comparar_importancia_fez(arquivo_csv):
    print(f"[*] Analisando assinatura quântica no FEZ: {arquivo_csv}...")
    if not os.path.exists(arquivo_csv):
        return

    df = pd.read_csv(arquivo_csv)
    # Aplicando a Pós-Seleção Crítica (Aharonov)
    df_pos = df[df['Q1_Futuro_T1'] == 1].copy()
    
    X, y = [], []
    for tipo, label in [('Placebo', 0), ('Ativo', 1)]:
        df_tipo = df_pos[df_pos['Tipo'] == tipo]['Q2_Espiao_T0'].values
        for i in range(0, len(df_tipo) - TAMANHO_JANELA, TAMANHO_JANELA):
            X.append(extrair_features(df_tipo[i:i+TAMANHO_JANELA]))
            y.append(label)
            
    X = np.array(X)
    y = np.array(y)
    
    nomes_features = ['Densidade P(1)', 'Entropia de Shannon', 'Taxa de Mudança (Flicker)']
    modelo = RandomForestClassifier(n_estimators=500, random_state=42, n_jobs=-1)
    modelo.fit(X, y)
    
    importancias = modelo.feature_importances_
    
    # Exibição dos valores exatos para a nossa Tabela Comparativa
    for nome, imp in zip(nomes_features, importancias):
        print(f" >> {nome}: {imp*100:.2f}%")
        
    # Geração do gráfico para o Apêndice do Artigo
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(8, 5))
    sns.barplot(x=importancias, y=nomes_features, palette="magma")
    plt.title('Assinatura de Importância - IBM FEZ', fontsize=14)
    plt.xlabel('Peso da Decisão', fontsize=12)
    plt.savefig("janus_importancia_fez.png", dpi=300)

if __name__ == "__main__":
    comparar_importancia_fez("AUDIT_REAL_ibm_fez.csv")