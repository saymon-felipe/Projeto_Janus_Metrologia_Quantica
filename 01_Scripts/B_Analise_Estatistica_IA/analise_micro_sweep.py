import pandas as pd
import numpy as np
from scipy.stats import entropy
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

print("\n==========================================================")
print(" 🔬 ANÁLISE JANUS: PREPARAÇÃO PARA A REDE NEURAL (CNN)")
print("==========================================================")

ARQUIVO = "dataset_micro_sweep_cnn.csv"
LIMIAR_POS_SELECAO = 0.70
NUM_PARES = 40

def extrair_features(bits):
    p1 = np.mean(bits)
    ent = entropy([1 - p1 + 1e-9, p1 + 1e-9], base=2)
    flicker = np.sum(np.abs(np.diff(bits))) / len(bits) if len(bits)>1 else 0
    return [p1, ent, flicker]

df = pd.read_csv(ARQUIVO)
resultados = []

for angulo, df_config in df.groupby('Angulo_Rad'):
    X, y = [], []
    shots_aprovados = 0
    
    for (shot, tipo), grupo in df_config.groupby(['Shot', 'Tipo']):
        bits_futuro = grupo.sort_values('ID_Par')['Q1_Futuro_T1'].values
        bits_espiao = grupo.sort_values('ID_Par')['Q2_Espiao_T0'].values
        
        if np.mean(bits_futuro) >= LIMIAR_POS_SELECAO:
            shots_aprovados += 1
            X.append(extrair_features(bits_espiao))
            y.append(0 if tipo == 'Placebo' else 1)
            
    if shots_aprovados < 50:
        continue
        
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    clf = RandomForestClassifier(n_estimators=300, max_depth=6, random_state=42)
    clf.fit(X_train, y_train)
    
    resultados.append({
        'Angulo': angulo, 
        'Precisao (%)': round(accuracy_score(y_test, clf.predict(X_test))*100, 2), 
        'Sobreviventes (Matrizes)': shots_aprovados
    })

print("\n🏆 RESULTADO DO MICRO-AJUSTE DA LENTE:")
print(pd.DataFrame(resultados).sort_values(by='Precisao (%)', ascending=False).to_string(index=False))