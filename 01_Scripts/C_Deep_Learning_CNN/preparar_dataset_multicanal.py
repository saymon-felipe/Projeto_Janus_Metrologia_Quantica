import pandas as pd
import numpy as np

def calcular_correlacao_local(matriz):
    """Cria um mapa de como cada qubit diverge da vizinhança."""
    correlacao = np.zeros_like(matriz, dtype=float)
    rows, cols = matriz.shape
    for r in range(rows):
        for c in range(cols):
            # Vizinhos (Cima, Baixo, Esquerda, Direita)
            vizinhos = []
            if r > 0: vizinhos.append(matriz[r-1, c])
            if r < rows-1: vizinhos.append(matriz[r+1, c])
            if c > 0: vizinhos.append(matriz[r, c-1])
            if c < cols-1: vizinhos.append(matriz[r, c+1])
            
            # Canal de Correlação: Valor absoluto da diferença para a média local
            correlacao[r, c] = np.abs(matriz[r, c] - np.mean(vizinhos))
    return correlacao

def aumentar_dados_multicanal(bits_5x8):
    # Canal 1: Bits / Canal 2: Correlação Local
    c1 = bits_5x8
    c2 = calcular_correlacao_local(c1)
    
    # Criar o bloco de 2 canais
    bloco = np.stack([c1, c2], axis=0) # Shape: (2, 5, 8)
    
    # Gerar simetrias (Espelhamentos)
    versoes = []
    versoes.append(bloco)
    versoes.append(np.flip(bloco, axis=1)) # Inversão Vertical
    versoes.append(np.flip(bloco, axis=2)) # Inversão Horizontal
    versoes.append(np.flip(np.flip(bloco, axis=1), axis=2))
    return versoes

# Carregamento e Processamento
df = pd.read_csv("dataset_laser_focus_cnn.csv")
LIMIAR = 0.70
X_multicanal, y_labels = [], []

for (shot, tipo), grupo in df.groupby(['Shot', 'Tipo']):
    grupo_ord = grupo.sort_values('ID_Par')
    futuro = grupo_ord['Q1_Futuro_T1'].values
    if np.mean(futuro) >= LIMIAR:
        espiao = grupo_ord['Q2_Espiao_T0'].values.reshape(5, 8)
        label = 1 if tipo == 'Ativo' else 0
        
        for v in aumentar_dados_multicanal(espiao):
            X_multicanal.append(v)
            y_labels.append(label)

X_multicanal = np.array(X_multicanal)
y_labels = np.array(y_labels)
np.save("X_janus_v2.npy", X_multicanal)
np.save("y_janus_v2.npy", y_labels)
print(f"[V] Dataset Multicanal expandido para {len(X_multicanal)} amostras!")