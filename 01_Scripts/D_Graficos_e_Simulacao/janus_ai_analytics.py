# janus_ai_analytics.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, roc_curve, auc
from scipy.stats import entropy
import os

TAMANHO_JANELA = 50

def extrair_features(valores_q2):
    prob_1 = np.mean(valores_q2)
    ent = entropy([prob_1, 1 - prob_1], base=2) if 0 < prob_1 < 1 else 0
    mudancas = np.sum(np.abs(np.diff(valores_q2))) / len(valores_q2)
    return [prob_1, ent, mudancas]

def gerar_analytics_ia(arquivo_csv):
    print(f"[*] Compilando evidências da máquina {arquivo_csv}...")
    if not os.path.exists(arquivo_csv):
        print(f" [X] Erro: {arquivo_csv} não encontrado.")
        return

    df = pd.read_csv(arquivo_csv)
    df_pos = df[df['Q1_Futuro_T1'] == 1].copy() # PÓS-SELEÇÃO
    
    X, y = [], []
    for tipo, label in [('Placebo', 0), ('Ativo', 1)]:
        df_tipo = df_pos[df_pos['Tipo'] == tipo]['Q2_Espiao_T0'].values
        for i in range(0, len(df_tipo) - TAMANHO_JANELA, TAMANHO_JANELA):
            X.append(extrair_features(df_tipo[i:i+TAMANHO_JANELA]))
            y.append(label)
            
    X = np.array(X)
    y = np.array(y)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    
    modelo = RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1)
    modelo.fit(X_train, y_train)
    
    y_pred = modelo.predict(X_test)
    y_prob = modelo.predict_proba(X_test)[:, 1]
    
    sns.set_theme(style="white")
    
    # 1. Matriz de Confusão
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False, annot_kws={"size": 14})
    plt.title('Matriz de Confusão - Inferência Passada', fontsize=14)
    plt.ylabel('Cenário Real (Futuro)', fontsize=12)
    plt.xlabel('Cenário Previsto (Lido no Passado)', fontsize=12)
    plt.xticks([0.5, 1.5], ['Placebo (Sem Marreta)', 'Ativo (Com Marreta)'])
    plt.yticks([0.5, 1.5], ['Placebo (Sem Marreta)', 'Ativo (Com Marreta)'])
    plt.tight_layout()
    plt.savefig("janus_matriz_confusao.png", dpi=300)
    plt.close()
    
    # 2. Curva ROC
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'Curva ROC (AUC = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Taxa de Falsos Positivos')
    plt.ylabel('Taxa de Verdadeiros Positivos')
    plt.title('Receiver Operating Characteristic (ROC)', fontsize=14)
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig("janus_curva_roc.png", dpi=300)
    plt.close()
    
    print(f"[*] Matriz de Confusão e Curva ROC geradas com sucesso (AUC: {roc_auc:.3f}).")

if __name__ == "__main__":
    gerar_analytics_ia("dataset_janus_massivo_ibm_kingston.csv") 