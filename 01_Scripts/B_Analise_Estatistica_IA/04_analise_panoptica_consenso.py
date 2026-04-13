import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
import scipy.stats

print("\n==========================================================")
print(" 🧠 ANÁLISE PANÓPTICO: O CONSENSO DOS ESPIÕES")
print("==========================================================")

ARQUIVO = "dataset_panoptico_ibm_fez.csv" 

try:
    df = pd.read_csv(ARQUIVO)
except:
    print("[X] Arquivo não encontrado.")
    exit()

# 1. PÓS-SELEÇÃO: O Filtro de Aharonov (Só universos onde o Futuro = 1)
df_pos = df[df['Q1_Futuro_T1'] == 1].copy()
print(f"[*] Filtro Aplicado (T1=1). Eventos restantes: {len(df_pos)} de {len(df)}")

# 2. ENGENHARIA DE FEATURES (Consenso)
# Calcular a "Intensidade do Sinal" somando a leitura dos 3 espiões.
# Pode ser 0 (Nenhum viu), 1, 2, ou 3 (Todos viram).
df_pos['Consenso'] = df_pos['Espiao_1'] + df_pos['Espiao_2'] + df_pos['Espiao_3']

# Agrupar em pequenas janelas para capturar o "Flicker do Consenso"
TAMANHO_JANELA = 16
X, y = [], []

for tipo in ['Placebo', 'Ativo']:
    dados_tipo = df_pos[df_pos['Tipo'] == tipo]['Consenso'].values
    label = 0 if tipo == 'Placebo' else 1
    
    for i in range(0, len(dados_tipo) - TAMANHO_JANELA, TAMANHO_JANELA):
        janela = dados_tipo[i : i + TAMANHO_JANELA]
        
        media_consenso = np.mean(janela)
        variancia_consenso = np.var(janela)
        flicker_consenso = np.sum(np.abs(np.diff(janela))) / len(janela)
        
        X.append([media_consenso, variancia_consenso, flicker_consenso])
        y.append(label)

X = np.array(X)
y = np.array(y)

print("\n[*] Treinando a IA para ler a 'votação' dos espiões...")
modelo = RandomForestClassifier(n_estimators=300, max_depth=8, random_state=42)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
pontuacoes = cross_val_score(modelo, X, y, cv=cv, scoring='accuracy')

media_precisao = np.mean(pontuacoes)
p_value = scipy.stats.ttest_1samp(pontuacoes, 0.50)[1]

print("\n==========================================================")
print(" 🔬 VEREDICTO DE CONSENSO (Múltiplos Espiões)")
print("==========================================================")
print(f" Precisão da IA : {media_precisao * 100:.2f}%")
print(f" P-Value        : {p_value:.6f}")
print("----------------------------------------------------------")

if media_precisao > 0.53 and p_value < 0.05:
    print(" [🚨] SINAL AMPLIFICADO!")
    print(" O uso de múltiplos espiões confirmou a queda de probabilidade.")
else:
    print(" [X] Colapso por Excesso de Medição.")
    print(" Os espiões foram gulosos demais e destruíram o entrelaçamento antes da marreta.")