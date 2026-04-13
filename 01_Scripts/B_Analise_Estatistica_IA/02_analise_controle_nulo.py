import pandas as pd
import numpy as np
import warnings
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
import scipy.stats

warnings.filterwarnings("ignore")

print("\n==========================================================")
print(" 🧠 PROJETO JANUS V29: IA COM PÓS-SELEÇÃO RETROCAUSAL")
print("==========================================================")

ARQUIVO_CSV = "dataset_nulo_sem_entrelaçamento_ibm_fez.csv" 
TAMANHO_JANELA = 32

try:
    df = pd.read_csv(ARQUIVO_CSV)
except Exception as e:
    print(f"[X] Arquivo não encontrado: {e}")
    exit()

# Pós-Seleção. 
df_pos_selecionado = df[df['Q1_Futuro_T1'] == 1].copy()

print(f"[*] Base de dados filtrada via Pós-Seleção do Futuro (T1 = 1).")
print(f"[*] Eventos restantes: {len(df_pos_selecionado)} de {len(df)}.")

df_placebo = df_pos_selecionado[df_pos_selecionado['Tipo'] == 'Placebo']['Q2_Espiao_T0'].values
df_ativo = df_pos_selecionado[df_pos_selecionado['Tipo'] == 'Ativo']['Q2_Espiao_T0'].values

def extrair_features(janela):
    densidade = np.mean(janela)
    p_1 = densidade if densidade > 0 else 0.001
    p_0 = (1.0 - p_1) if p_1 < 1 else 0.001
    entropia = - (p_1 * np.log2(p_1) + p_0 * np.log2(p_0))
    taxa_mudanca = np.sum(np.abs(np.diff(janela))) / len(janela)
    return [densidade, entropia, taxa_mudanca]

X, y = [], []

# Montar Janelas (Placebo)
for i in range(0, len(df_placebo) - TAMANHO_JANELA, TAMANHO_JANELA):
    X.append(extrair_features(df_placebo[i : i + TAMANHO_JANELA]))
    y.append(0)

# Montar Janelas (Ativo - Com Marreta no Futuro)
for i in range(0, len(df_ativo) - TAMANHO_JANELA, TAMANHO_JANELA):
    X.append(extrair_features(df_ativo[i : i + TAMANHO_JANELA]))
    y.append(1)

X = np.array(X)
y = np.array(y)

print(f"[*] Treinando a IA para encontrar as sombras temporais nos dados do Espião...")

modelo = RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
pontuacoes = cross_val_score(modelo, X, y, cv=cv, scoring='accuracy')

media_precisao = np.mean(pontuacoes)
desvio_padrao = np.std(pontuacoes)

_, p_value = scipy.stats.ttest_1samp(pontuacoes, 0.50)

print("\n==========================================================")
print(" 🔬 O VEREDICTO DE AHARONOV (DOIS VETORES)")
print("==========================================================")
print(f" Precisão da IA (Olhando só para o Passado Fraco): {media_precisao * 100:.2f}%")
print(f" Margem de Flutuação (Desvio)                    : ± {desvio_padrao * 100:.2f}%")
print(f" P-Value                                         : {p_value:.6f}")
print("----------------------------------------------------------")

if media_precisao > 0.53 and p_value < 0.05:
    print(" [🚨] ANOMALIA DE VALOR FRACO CONFIRMADA!")
    print(" Condicionado a um resultado futuro, a IA conseguiu prever a")
    print(" presença da marreta olhando apenas para as medições fracas no passado.")
else:
    print(" [X] A TEORIA FECHOU-SE. O TEMPO É LINEAR.")
    print(" Mesmo com medição fraca e pós-seleção condicionada (Aharonov),")
    print(" a IA não conseguiu distinguir o passado dos dois universos.")
print("==========================================================")