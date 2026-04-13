# janus_plot_distributions.py
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import entropy
import os

TAMANHO_JANELA = 50

def extrair_features(valores_q2):
    prob_1 = np.mean(valores_q2)
    ent = entropy([prob_1, 1 - prob_1], base=2) if 0 < prob_1 < 1 else 0
    return prob_1, ent

def processar_dataset(arquivo_csv, nome_cenario):
    print(f"[*] Processando {arquivo_csv}...")
    if not os.path.exists(arquivo_csv):
        print(f" [X] Erro: {arquivo_csv} não encontrado.")
        return pd.DataFrame()

    df = pd.read_csv(arquivo_csv)
    df_pos = df[df['Q1_Futuro_T1'] == 1].copy() # Pós-Seleção Ativa
    
    dados_extraidos = []
    # Usaremos os dados da classe 'Ativo' (onde a marreta teórica existe) para comparar cenários
    df_ativo = df_pos[df_pos['Tipo'] == 'Ativo']['Q2_Espiao_T0'].values
    
    for i in range(0, len(df_ativo) - TAMANHO_JANELA, TAMANHO_JANELA):
        janela = df_ativo[i:i+TAMANHO_JANELA]
        prob_1, ent = extrair_features(janela)
        dados_extraidos.append({
            'Cenário': nome_cenario,
            'Entropia (Espião)': ent,
            'Densidade P(1)': prob_1
        })
        
    return pd.DataFrame(dados_extraidos)

def gerar_graficos():
    # 1. Extração de Dados
    df_real = processar_dataset("AUDIT_REAL_ibm_kingston.csv", "Teste Real (Retrocausal)")
    df_phantom = processar_dataset("AUDIT_PHAN_ibm_kingston.csv", "Teste Fantasma (Silêncio)")
    
    if df_real.empty or df_phantom.empty:
        return
        
    df_plot = pd.concat([df_real, df_phantom])
    
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # 2. Gráfico de Violino (Entropia)
    sns.violinplot(data=df_plot, x='Cenário', y='Entropia (Espião)', inner="quart", ax=axes[0], palette="muted")
    axes[0].set_title('Modulação Entrópica no Passado', fontsize=14)
    axes[0].set_ylabel('Entropia de Shannon (Bits)')
    
    # 3. Gráfico KDE (Densidade de Probabilidade)
    sns.kdeplot(data=df_real, x='Densidade P(1)', fill=True, label='Sinal Real', ax=axes[1], color='crimson')
    sns.kdeplot(data=df_phantom, x='Densidade P(1)', fill=True, label='Ruído Fantasma', ax=axes[1], color='gray')
    axes[1].set_title('Desvio da Distribuição de P(1)', fontsize=14)
    axes[1].set_xlabel('Probabilidade Média P(1) no Q2')
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig("janus_distribuicao_retrocausal.png", dpi=300)
    print("[*] Veredicto visual gerado: janus_distribuicao_retrocausal.png")

if __name__ == "__main__":
    gerar_graficos()