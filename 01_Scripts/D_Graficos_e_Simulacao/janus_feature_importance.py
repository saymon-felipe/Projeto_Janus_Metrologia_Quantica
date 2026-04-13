# janus_feature_importance.py
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

def gerar_grafico_importancia(arquivo_csv):
    print(f"[*] Analisando pesos das variáveis em {arquivo_csv}...")
    if not os.path.exists(arquivo_csv):
        print(f" [X] Erro: {arquivo_csv} não encontrado.")
        return

    df = pd.read_csv(arquivo_csv)
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
    
    # Treino da IA
    modelo = RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1)
    modelo.fit(X, y)
    
    # Extração das Importâncias
    importancias = modelo.feature_importances_
    
    # Renderização Gráfica
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(8, 5))
    
    sns.barplot(x=importancias, y=nomes_features, palette="viridis")
    
    plt.title('Importância das Variáveis no Sinal Retrocausal', fontsize=14)
    plt.xlabel('Peso da Decisão (Importância Relativa)', fontsize=12)
    plt.ylabel('Variáveis do Passado (Q2)', fontsize=12)
    
    plt.tight_layout()
    plt.savefig("janus_importancia_variaveis.png", dpi=300)
    print("[*] Gráfico gerado com sucesso: janus_importancia_variaveis.png")

if __name__ == "__main__":
    gerar_grafico_importancia("AUDIT_REAL_ibm_kingston.csv")