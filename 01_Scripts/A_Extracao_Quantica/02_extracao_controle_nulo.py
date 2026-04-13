import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
import os
from dotenv import load_dotenv
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

print("\n==========================================================")
print(" ✂️ PROJETO JANUS V30: O TESTE DO FALSO POSITIVO (NULL TEST)")
print("==========================================================")

load_dotenv()

TOKEN_IBM = os.getenv("IBM_QUANTUM_TOKEN")

try:
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=TOKEN_IBM)
    NOME_DA_MAQUINA = "ibm_fez"
    backend = service.backend(NOME_DA_MAQUINA)
    print(f"[*] Conectado ao Processador Quântico: {backend.name}")
except Exception as e:
    print(f"[X] Erro Crítico: {e}")
    exit()

def montar_experimentos_nulos():
    theta = np.pi / 8  
    
    # ==========================================
    # CIRCUITO PLACEBO NULO (Sem Entrelaçamento)
    # ==========================================
    qc_p = QuantumCircuit(3, 3)
    qc_p.h(0)                   
    qc_p.h(1)
    
    qc_p.barrier()
    qc_p.cry(theta, 0, 2)       # Medição Fraca (O Espião olha para o Q0)
    qc_p.measure(2, 2)          
    
    qc_p.barrier()
    qc_p.measure(1, 1)          
    qc_p.measure(0, 0)          

    # ==========================================
    # CIRCUITO ATIVO NULO (Marreta no Futuro, mas sem Entrelaçamento)
    # ==========================================
    qc_a = QuantumCircuit(3, 3)
    qc_a.h(0)
    qc_a.h(1)
    
    qc_a.barrier()
    qc_a.cry(theta, 0, 2)
    qc_a.measure(2, 2)          
    
    qc_a.barrier()
    qc_a.rx(np.pi/2, 1)         # A MARRETA BATE NO FUTURO (Mas o Q1 está isolado)
    
    qc_a.measure(1, 1)          
    qc_a.measure(0, 0)          

    return [qc_p, qc_a]

circuitos = montar_experimentos_nulos()
circuitos_isa = transpile(circuitos, backend=backend)

SHOTS_POR_LOTE = 4096
NUM_LOTES = 5 
dados_finais = []
sampler = Sampler(backend)

print(f"\n[*] Iniciando extração de Controle Nulo ({NUM_LOTES} lotes)...")

for lote in range(NUM_LOTES):
    print(f"    -> Lote Nulo {lote + 1}/{NUM_LOTES}...")
    try:
        job = sampler.run(circuitos_isa, shots=SHOTS_POR_LOTE)
        result = job.result()
        
        bits_p = result[0].data.c.get_bitstrings()
        bits_a = result[1].data.c.get_bitstrings()
        
        for i in range(SHOTS_POR_LOTE):
            dados_finais.append({'Tipo': 'Placebo', 'Q2_Espiao_T0': int(bits_p[i][0]), 'Q1_Futuro_T1': int(bits_p[i][1])})
            dados_finais.append({'Tipo': 'Ativo', 'Q2_Espiao_T0': int(bits_a[i][0]), 'Q1_Futuro_T1': int(bits_a[i][1])})
    except Exception as e:
        print(f"    [X] Erro: {e}")

nome_arquivo = f"dataset_nulo_sem_entrelaçamento_{backend.name}.csv"
pd.DataFrame(dados_finais).to_csv(nome_arquivo, index=False)
print(f"\n[V] Arquivo {nome_arquivo} gerado.")