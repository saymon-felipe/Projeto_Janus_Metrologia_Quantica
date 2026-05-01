import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis
import warnings

warnings.filterwarnings('ignore')

print("\n==========================================================")
print(" 👁️ PROJETO JANUS V8: DECODIFICADOR FEC MATEMÁTICO")
print("==========================================================")

arquivo_mensagem = "janus_sinal_v8.csv"
ALFABETO = " ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def extrair_features(vetor):
    return np.array([np.mean(vetor), np.var(vetor), skew(vetor), kurtosis(vetor)])

try:
    df = pd.read_csv(arquivo_mensagem)
    df_v = df[df['q1_futuro'] == 1].copy()
    df_v['consenso'] = df_v['espiao_1'] + df_v['espiao_2'] + df_v['espiao_3']
except Exception as e:
    print(f"[X] Erro ao carregar: {e}"); exit()

assinaturas_blocos = []
for i in sorted(df_v['ordem_sequencia'].unique()):
    bloco = df_v[df_v['ordem_sequencia'] == i]['consenso'].values
    assinaturas_blocos.append(extrair_features(bloco) if len(bloco) > 0 else np.zeros(4))

if len(assinaturas_blocos) < 13:
    print("[X] Arquivo insuficiente."); exit()

# 1. CALIBRAÇÃO (Handshake '0101')
assinatura_0 = np.mean([assinaturas_blocos[0], assinaturas_blocos[2]], axis=0)
assinatura_1 = np.mean([assinaturas_blocos[1], assinaturas_blocos[3]], axis=0)

# 2. DEMODULAÇÃO
bits_recebidos = ""
for feat in assinaturas_blocos[4:]:
    d0 = np.linalg.norm(feat - assinatura_0)
    d1 = np.linalg.norm(feat - assinatura_1)
    bits_recebidos += '0' if d0 < d1 else '1'

# 3. REVERSÃO DO INTERLEAVING
num_caracteres = len(bits_recebidos) // 9
blocos_reconstruidos = ["" for _ in range(num_caracteres)]

idx = 0
for bit_idx in range(9):
    for char_idx in range(num_caracteres):
        blocos_reconstruidos[char_idx] += bits_recebidos[idx]
        idx += 1

print(f"[*] Blocos Reconstruídos : {blocos_reconstruidos}")

# 4. CORREÇÃO HAMMING (9,5) E TRADUÇÃO
def decodificar_hamming(bloco_9):
    b = [int(x) for x in bloco_9]
    # Cálculo do Síndrome para encontrar o erro
    s1 = b[0] ^ b[2] ^ b[4] ^ b[6] ^ b[8]
    s2 = b[1] ^ b[2] ^ b[5] ^ b[6]
    s4 = b[3] ^ b[4] ^ b[5] ^ b[6]
    s8 = b[7] ^ b[8]
    
    sindrome = s1*1 + s2*2 + s4*4 + s8*8
    
    if sindrome != 0 and sindrome <= 9:
        print(f"    [!] Erro detectado no bit {sindrome}. Corrigindo automaticamente.")
        b[sindrome - 1] ^= 1 # Inverte o bit danificado
        
    # Extrai os dados: P1, P2, D1, P4, D2, D3, D4, P8, D5
    dados_5_bits = f"{b[2]}{b[4]}{b[5]}{b[6]}{b[8]}"
    return dados_5_bits

mensagem_final = ""
for bloco in blocos_reconstruidos:
    bits_dados = decodificar_hamming(bloco)
    idx_char = int(bits_dados, 2)
    mensagem_final += ALFABETO[idx_char] if idx_char < len(ALFABETO) else "?"

print("\n==========================================================")
print(" 📨 MENSAGEM FINAL V8 (DESCOMPRIMIDA)")
print("==========================================================")
print(f" TEXTO TRADUZIDO : {mensagem_final}")
print("==========================================================\n")