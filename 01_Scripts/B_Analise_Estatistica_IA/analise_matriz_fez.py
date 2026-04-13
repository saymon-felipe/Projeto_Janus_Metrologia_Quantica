"""
PROJETO JANUS - FASE 2: ANÁLISE DA MATRIZ ESPACIAL (120 QUBITS)
Motor de Inteligência Artificial para deteção do sinal retrocausal em topologia de rede.
"""
import os
import numpy as np
import pandas as pd
from scipy.stats import entropy
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

ARQUIVO_DADOS = "dataset_matriz_espacial.csv"

LIMIAR_POS_SELECAO = 0.60  

def calcular_entropia_espacial(bits):
    """Calcula a desordem do array de 40 qubits no exato momento do disparo."""
    p1 = np.mean(bits)
    p0 = 1 - p1
    # Adicionamos 1e-9 para evitar erro de divisão por zero ou log(0)
    return entropy([p0 + 1e-9, p1 + 1e-9], base=2)

def calcular_flicker_espacial(bits):
    """Calcula a taxa de variação lateral (qubits vizinhos mudando de estado)."""
    if len(bits) <= 1:
        return 0
    diferencas = np.abs(np.diff(bits))
    return np.sum(diferencas) / len(bits)

def executar_analise(arquivo_csv):
    print("==========================================================")
    print(" 🧠 MOTOR DE ANÁLISE JANUS: MATRIZ ESPACIAL")
    print("==========================================================")

    if not os.path.exists(arquivo_csv):
        print(f"[X] ERRO: O ficheiro {arquivo_csv} não foi encontrado.")
        print("    Aguarde a finalização do script de extração.")
        return

    print(f"[*] A carregar dados brutos de {arquivo_csv}...")
    df = pd.read_csv(arquivo_csv)
    
    print("[*] A reconstruir snapshots espaciais (agrupando por Lote e Shot)...")
    # Agrupamos os dados para juntar as 40 linhas de cada disparo numa única matriz
    grupos = df.groupby(['Lote', 'Shot', 'Tipo'])
    
    X = []
    y = []
    
    total_shots = 0
    shots_aprovados = 0

    print(f"[*] A aplicar Pós-Seleção (Filtro do Futuro >= {LIMIAR_POS_SELECAO*100}%)...")
    
    for (lote, shot, tipo), grupo in grupos:
        total_shots += 1
        
        # Garante a ordem correta dos pares (0 a 39)
        grupo_ordenado = grupo.sort_values('ID_Par')
        
        # Arrays daquele milissegundo exato
        bits_futuro = grupo_ordenado['Q1_Futuro_T1'].values
        bits_espiao = grupo_ordenado['Q2_Espiao_T0'].values
        
        # Verifica se a "Marreta" foi bem sucedida na maioria da matriz
        sucesso_futuro = np.mean(bits_futuro)
        
        if sucesso_futuro >= LIMIAR_POS_SELECAO:
            shots_aprovados += 1
            
            # 1. Extração de Características Espaciais (As 3 "Texturas")
            densidade = np.mean(bits_espiao)
            ent = calcular_entropia_espacial(bits_espiao)
            flicker = calcular_flicker_espacial(bits_espiao)
            
            X.append([densidade, ent, flicker])
            
            # 2. Rotulagem
            # 0 = Placebo (Sem intervenção real, apenas ruído)
            # 1 = Ativo (Futuro foi martelado, possível retrocausalidade presente)
            y.append(0 if tipo == 'Placebo' else 1)
            
    print(f"    -> Total de Disparos Processados: {total_shots}")
    print(f"    -> Sobreviventes à Pós-Seleção: {shots_aprovados}")
    
    if shots_aprovados < 100:
        print("\n[!] AVISO CRÍTICO: Dados insuficientes após o filtro do futuro.")
        print("    A 'marreta' falhou muito devido a ruído ou o limiar está muito alto.")
        return

    print("\n[*] A inicializar a Random Forest (Floresta Aleatória)...")
    
    # Divisão 70% Treino / 30% Teste
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    # Configuração robusta para evitar overfitting em dados quânticos ruidosos
    clf = RandomForestClassifier(
        n_estimators=300, 
        max_depth=6, 
        min_samples_leaf=4,
        random_state=42
    )
    
    clf.fit(X_train, y_train)
    previsoes = clf.predict(X_test)
    
    precisao = accuracy_score(y_test, previsoes)
    importancias = clf.feature_importances_
    
    print("\n==========================================================")
    print(" 🏆 VEREDICTO FINAL: RESULTADOS DA MATRIZ JANUS")
    print("==========================================================")
    print(f"  [+] Precisão de Deteção: {precisao * 100:.2f}%")
    print("      (Acima de ~52% indica superação do acaso clássico)")
    
    print("\n  [+] Peso Físico das Características (O que a IA viu):")
    print(f"      - Densidade P(1): {importancias[0]*100:.2f}% (Alteração Absoluta)")
    print(f"      - Entropia:       {importancias[1]*100:.2f}% (Alteração do Caos)")
    print(f"      - Flicker:        {importancias[2]*100:.2f}% (Frequência Espacial)")
    print("==========================================================\n")

if __name__ == "__main__":
    executar_analise(ARQUIVO_DADOS)