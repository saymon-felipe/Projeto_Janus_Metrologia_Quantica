import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import skew, kurtosis
import warnings

warnings.filterwarnings('ignore')

sns.set_theme(style="darkgrid")
plt.rcParams['font.family'] = 'monospace'

def extrair_features(vetor):
    if len(vetor) == 0:
        return np.zeros(4)
    return np.array([np.mean(vetor), np.var(vetor), skew(vetor), kurtosis(vetor)])

def gerar_graficos_v8(arquivo_csv):
    try:
        df = pd.read_csv(arquivo_csv)
    except FileNotFoundError:
        print(f"[X] Arquivo {arquivo_csv} não encontrado.")
        return

    df_v = df[df['q1_futuro'] == 1].copy()
    df_v['consenso'] = df_v['espiao_1'] + df_v['espiao_2'] + df_v['espiao_3']

    assinaturas_blocos = []
    medias_consenso = []
    ordens = sorted(df_v['ordem_sequencia'].unique())
    
    for i in ordens:
        bloco = df_v[df_v['ordem_sequencia'] == i]['consenso'].values
        feat = extrair_features(bloco)
        assinaturas_blocos.append(feat)
        medias_consenso.append(feat[0])

    if len(assinaturas_blocos) < 5:
        print("[X] Dados insuficientes para calibração.")
        return

    assinatura_0 = np.mean([assinaturas_blocos[0], assinaturas_blocos[2]], axis=0)
    assinatura_1 = np.mean([assinaturas_blocos[1], assinaturas_blocos[3]], axis=0)

    distancias_0 = []
    distancias_1 = []
    bits_preditos = []

    for feat in assinaturas_blocos[4:]:
        d0 = np.linalg.norm(feat - assinatura_0)
        d1 = np.linalg.norm(feat - assinatura_1)
        distancias_0.append(d0)
        distancias_1.append(d1)
        bits_preditos.append(0 if d0 < d1 else 1)

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('PROJETO JANUS V8 - TELEMETRIA E SINAL RETROCAUSAL', fontsize=16, fontweight='bold')

    ax1 = axes[0, 0]
    ax1.plot(ordens, medias_consenso, marker='o', linestyle='-', color='#1f77b4', alpha=0.8)
    ax1.axvline(x=3.5, color='red', linestyle='--', label='Fim do Handshake')
    ax1.set_title('Estabilidade Termodinâmica (Média do Consenso)')
    ax1.set_xlabel('Ordem da Sequência Temporal (Passos)')
    ax1.set_ylabel('Amplitude Média (Pós-Seleção)')
    ax1.legend()

    ax2 = axes[0, 1]
    x_bits = range(4, len(assinaturas_blocos))
    ax2.plot(x_bits, distancias_0, label='Distância para "0"', color='blue', alpha=0.7)
    ax2.plot(x_bits, distancias_1, label='Distância para "1"', color='orange', alpha=0.7)
    ax2.set_title('Demodulação: Separação Vetorial das Assinaturas')
    ax2.set_xlabel('Índice do Bit Recebido')
    ax2.set_ylabel('Distância Euclidiana')
    ax2.legend()

    ax3 = axes[1, 0]
    cores = ['blue' if b == 0 else 'orange' for b in bits_preditos]
    ax3.scatter(distancias_0, distancias_1, c=cores, s=60, alpha=0.8, edgecolor='k')
    limite_max = max(max(distancias_0), max(distancias_1)) if distancias_0 else 1
    ax3.plot([0, limite_max], [0, limite_max], 'r--', alpha=0.5, label='Fronteira de Decisão')
    ax3.set_title('Espaço de Decisão (Azul=0, Laranja=1)')
    ax3.set_xlabel('Distância para "0"')
    ax3.set_ylabel('Distância para "1"')
    ax3.legend()

    ax4 = axes[1, 1]
    margem_confianca = np.abs(np.array(distancias_0) - np.array(distancias_1))
    sns.histplot(margem_confianca, bins=15, kde=True, ax=ax4, color='purple')
    ax4.set_title('Força do Sinal (Margem Delta |D0 - D1|)')
    ax4.set_xlabel('Diferença Euclidiana Absoluta')
    ax4.set_ylabel('Densidade (Bits)')

    plt.tight_layout()
    plt.savefig('janus_v8_telemetria_dashboard.png', dpi=300, bbox_inches='tight')
    print("\n[V] Dashboard exportado: 'janus_v8_telemetria_dashboard.png'")

if __name__ == "__main__":
    gerar_graficos_v8("janus_sinal_v8_STEINSGATE_STEINRGATE.csv")