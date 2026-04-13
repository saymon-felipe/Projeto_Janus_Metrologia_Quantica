import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
import os
from dotenv import load_dotenv
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

print("\n==========================================================")
print(" 🌌 PROJETO JANUS: A MATRIZ ESPACIAL (120 QUBITS)")
print("==========================================================")

load_dotenv()

TOKEN_IBM = os.getenv("IBM_QUANTUM_TOKEN")

NOME_DA_MAQUINA = "ibm_fez"

try:
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=TOKEN_IBM)
    backend = service.backend(NOME_DA_MAQUINA)
    print(f"[*] Conectado ao Frigorífico Quântico: {backend.name} ({backend.num_qubits} qubits)")
except Exception as e:
    print(f"[X] Erro Crítico de Conexão: {e}")
    exit()

NUM_PARES = 40  # 40 células Janus * 3 qubits = 120 qubits no chip
TOTAL_QUBITS = NUM_PARES * 3

def montar_matriz_janus():
    theta = np.pi / 8  # A Sonda Fantasma (22.5 graus)
    
    # Criamos dois circuitos gigantes, cada um com 120 qubits e 120 bits clássicos
    qc_p = QuantumCircuit(TOTAL_QUBITS, TOTAL_QUBITS)
    qc_a = QuantumCircuit(TOTAL_QUBITS, TOTAL_QUBITS)
    
    for i in range(NUM_PARES):
        # Mapeamento: Cada par 'i' recebe 3 qubits sequenciais
        q0 = i * 3      # Passado
        q1 = i * 3 + 1  # Futuro
        q2 = i * 3 + 2  # Espião
        
        # --- PREPARAÇÃO DO PLACEBO ---
        qc_p.h(q0)
        qc_p.cx(q0, q1)
        qc_p.cry(theta, q0, q2)      # Espião lê o Passado
        qc_p.measure(q2, q2)         # Grava Q2
        qc_p.measure(q1, q1)         # Grava Q1 (Sem Marreta)
        qc_p.measure(q0, q0)         # Grava Q0
        
        # --- PREPARAÇÃO DO ATIVO ---
        qc_a.h(q0)
        qc_a.cx(q0, q1)
        qc_a.cry(theta, q0, q2)      # Espião lê o Passado
        qc_a.measure(q2, q2)         # Grava Q2
        
        qc_a.rx(np.pi/2, q1)         # A MARRETA NO FUTURO
        
        qc_a.measure(q1, q1)         # Grava Q1 (Futuro Alterado)
        qc_a.measure(q0, q0)         # Grava Q0

    return [qc_p, qc_a]

circuitos = montar_matriz_janus()

print(f"[*] Compilando matriz de {TOTAL_QUBITS} qubits para o formato físico do chip (isso pode demorar)...")

circuitos_isa = transpile(circuitos, backend=backend, optimization_level=3)

SHOTS_POR_LOTE = 2000
NUM_LOTES = 5 
sampler = Sampler(backend)

nome_arquivo = f"dataset_matriz_espacial_{backend.name}.csv"

print(f"\n[*] Iniciando extração espacial ({NUM_LOTES} lotes de {SHOTS_POR_LOTE} shots)...")

for lote in range(NUM_LOTES):
    print(f"    -> Disparando Lote {lote + 1}/{NUM_LOTES}...")
    dados_lote = [] 
    
    try:
        job = sampler.run(circuitos_isa, shots=SHOTS_POR_LOTE)
        print(f"       [A aguardar IBM - Job ID: {job.job_id()}]")
        
        result = job.result() 
        print("       [Processando payload de bits...]")
        
        # Extração
        bits_p = result[0].data.c.get_bitstrings()
        bits_a = result[1].data.c.get_bitstrings()
        
        for i in range(SHOTS_POR_LOTE):
            str_p = bits_p[i][::-1]
            str_a = bits_a[i][::-1]
            
            for par in range(NUM_PARES):
                idx0 = par * 3
                idx1 = par * 3 + 1
                idx2 = par * 3 + 2
                
                # Salvando os dados Placebo
                dados_lote.append({
                    'Lote': lote, 'Shot': i, 'ID_Par': par, 'Tipo': 'Placebo',
                    'Q2_Espiao_T0': int(str_p[idx2]), 
                    'Q1_Futuro_T1': int(str_p[idx1]),
                    'Q0_Forte_Fim': int(str_p[idx0])
                })
                
                # Salvando os dados Ativos
                dados_lote.append({
                    'Lote': lote, 'Shot': i, 'ID_Par': par, 'Tipo': 'Ativo',
                    'Q2_Espiao_T0': int(str_a[idx2]), 
                    'Q1_Futuro_T1': int(str_a[idx1]),
                    'Q0_Forte_Fim': int(str_a[idx0])
                })
        
        df_lote = pd.DataFrame(dados_lote)
        
        if lote == 0:
            df_lote.to_csv(nome_arquivo, index=False, mode='w')
        else:
            df_lote.to_csv(nome_arquivo, index=False, mode='a', header=False)
            
        print(f"       [V] Lote {lote + 1} salvo no disco! RAM libertada.")
            
    except Exception as e:
        print(f"    [X] Erro de execução no lote {lote + 1}: {e}")
        print("    [!] A continuar para o próximo lote para não interromper a extração...")

total_linhas_esperadas = NUM_LOTES * SHOTS_POR_LOTE * NUM_PARES * 2 

print("\n==========================================================")
print(f"[V] Extração Concluída!")
print(f"    Total teórico de linhas extraídas: {total_linhas_esperadas}")
print(f"    Arquivo preservado de forma incremental: {nome_arquivo}")
print("==========================================================")