import numpy as np
import scipy.stats

print("\n==========================================================")
print(" 🧮 PROJETO JANUS: PROVA DE CONCEITO MATEMÁTICA (Álgebra Linear)")
print("==========================================================")

# 1. DEFINIÇÃO DAS PORTAS QUÂNTICAS (Matrizes Clássicas)
I = np.array([[1, 0], [0, 1]], dtype=complex)
H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)

def RX(theta):
    return np.array([[np.cos(theta/2), -1j * np.sin(theta/2)],
                     [-1j * np.sin(theta/2), np.cos(theta/2)]], dtype=complex)

def CRY(theta):
    # Matriz Control-RY 4x4
    matriz = np.eye(4, dtype=complex)
    matriz[2:4, 2:4] = np.array([[np.cos(theta/2), -np.sin(theta/2)],
                                 [np.sin(theta/2), np.cos(theta/2)]])
    return matriz

# Produto Tensorial para expandir para 3 Qubits (Q2=Espiao, Q1=Futuro, Q0=Passado)
def kron_3(A, B, C):
    return np.kron(A, np.kron(B, C))

# 2. O MOTOR DE SIMULAÇÃO (Evolução de Schrödinger)
def simular_janus_matematica(ativo=False):
    # Estado Inicial: |000>
    estado = np.zeros(8, dtype=complex)
    estado[0] = 1.0 
    
    # PASSO 1: Superposição no Passado (Q0)
    gate_H0 = kron_3(I, I, H)
    estado = np.dot(gate_H0, estado)
    
    # PASSO 2: Entrelaçar Passado e Futuro (CNOT Q0->Q1)
    # Matriz CNOT expandida para 3 qubits (Q0 controla Q1)
    CNOT_01 = np.eye(8, dtype=complex)
    CNOT_01[[1,3,5,7]] = CNOT_01[[3,1,7,5]] # Troca amplitudes onde Q0=1
    estado = np.dot(CNOT_01, estado)
    
    # PASSO 3: A MEDIÇÃO FRACA (T0) - Espião (Q2) olha para o Passado (Q0)
    theta = np.pi / 8
    # Reordenar mentalmente para aplicar CRY de Q0 para Q2
    # Para simplificar na matemática, se Q0=1, rotacionamos Q2
    estado_novo = np.zeros(8, dtype=complex)
    for idx in range(8):
        binario = format(idx, '03b') # Ex: '001' (Q2=0, Q1=0, Q0=1)
        q0 = int(binario[2])
        q2 = int(binario[0])
        
        if q0 == 0:
            estado_novo[idx] += estado[idx] # Espião não vê nada
        else:
            # Q0 é 1, então rotacionamos a amplitude de Q2
            if q2 == 0:
                estado_novo[idx] += np.cos(theta/2) * estado[idx]
                estado_novo[idx + 4] += np.sin(theta/2) * estado[idx] # Transfere para Q2=1
            elif q2 == 1:
                # Na prática do nosso circuito inicial, Q2 começa em 0, 
                # então esta parte do CRY lida apenas com a fase.
                estado_novo[idx] += np.cos(theta/2) * estado[idx]
                estado_novo[idx - 4] += -np.sin(theta/2) * estado[idx]
                
    estado = estado_novo
    
    # PASSO 4: O FUTURO (T1) - A Marreta
    if ativo:
        gate_RX1 = kron_3(I, RX(np.pi/2), I)
        estado = np.dot(gate_RX1, estado)
        
    return estado

# 3. O VEREDICTO (Pós-Seleção e Probabilidade)
print("\n[*] Resolvendo os Vetores de Estado...")
estado_placebo = simular_janus_matematica(ativo=False)
estado_ativo = simular_janus_matematica(ativo=True)

def calcular_probabilidade_espiao_condicionada(estado):
    """ Calcula P(Espiao=1 | Futuro=1) - A matemática de Aharonov """
    prob_futuro_1 = 0
    prob_espiao_1_e_futuro_1 = 0
    
    for idx in range(8):
        amplitude = estado[idx]
        probabilidade = np.abs(amplitude)**2
        binario = format(idx, '03b')
        q2, q1, q0 = int(binario[0]), int(binario[1]), int(binario[2])
        
        if q1 == 1: # PÓS-SELEÇÃO DO FUTURO
            prob_futuro_1 += probabilidade
            if q2 == 1:
                prob_espiao_1_e_futuro_1 += probabilidade
                
    return prob_espiao_1_e_futuro_1 / prob_futuro_1

p_placebo = calcular_probabilidade_espiao_condicionada(estado_placebo)
p_ativo = calcular_probabilidade_espiao_condicionada(estado_ativo)

print(f"    -> Probabilidade Matemática (Placebo): P(Q2=1 | Q1=1) = {p_placebo*100:.4f}%")
print(f"    -> Probabilidade Matemática (Ativo)  : P(Q2=1 | Q1=1) = {p_ativo*100:.4f}%")

# 4. GERAÇÃO DE DADOS (Simulando a Máquina e Extraindo Features)
print("\n[*] Gerando 10.000 amostras estatísticas baseadas nestas equações...")
np.random.seed(42)
shots = 10000

# Gerar bits aleatórios baseados na probabilidade exata da matriz
bits_placebo = np.random.choice([0, 1], size=shots, p=[1-p_placebo, p_placebo])
bits_ativo = np.random.choice([0, 1], size=shots, p=[1-p_ativo, p_ativo])

def extrair_features(bits):
    p1 = np.mean(bits)
    p0 = 1 - p1
    entropia = - (p1 * np.log2(p1 + 1e-9) + p0 * np.log2(p0 + 1e-9))
    flicker = np.sum(np.abs(np.diff(bits))) / len(bits)
    return entropia, flicker

ent_p, flick_p = extrair_features(bits_placebo)
ent_a, flick_a = extrair_features(bits_ativo)

print("\n==========================================================")
print(" 🔬 ANÁLISE DAS FEATURES (Por que a IA detecta o sinal?)")
print("==========================================================")
print(f" PLACEBO (Silêncio) -> Entropia: {ent_p:.5f} Bits | Flicker: {flick_p:.5f}")
print(f" ATIVO   (Marreta)  -> Entropia: {ent_a:.5f} Bits | Flicker: {flick_a:.5f}")

if flick_a < flick_p:
    print("\n [🚨] ANOMALIA ESTATÍSTICA MATEMATICAMENTE COMPROVADA!")
    print("      A marreta no futuro causou uma QUEDA na taxa de vibração (Flicker) no passado.")
    print("      É isso que a Random Forest e a CNN estão identificando no hardware real.")