import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
import os
from dotenv import load_dotenv
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

print("\n==========================================================")
print(" 🛸 PROJETO JANUS V28: EXTRAÇÃO POR MEDIÇÃO FRACA (TSVF)")
print("==========================================================")

load_dotenv()

TOKEN_IBM = os.getenv("IBM_QUANTUM_TOKEN")

try:
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=TOKEN_IBM)
    NOME_DA_MAQUINA = "ibm_fez"
    backend = service.backend(NOME_DA_MAQUINA)
    print(f"[*] Conectado ao Frigorífico Quântico: {backend.name}")
except Exception as e:
    print(f"[X] Erro Crítico: {e}")
    exit()

def montar_experimentos_fracos():
    theta = np.pi / 8  # O Esbarrão Fraco (22.5 graus) - Lê a info sem colapsar a onda
    
    # ==========================================
    # CIRCUITO PLACEBO (Silêncio no Futuro)
    # ==========================================
    qc_p = QuantumCircuit(3, 3) # 3 Qubits, 3 Bits Clássicos
    qc_p.h(0)                   # Superposição do Passado (Q0)
    qc_p.cx(0, 1)               # Entrelaçamento Passado (Q0) e Futuro (Q1)
    
    qc_p.barrier()
    # A MEDIÇÃO FRACA (T0)
    qc_p.cry(theta, 0, 2)       # O Espião (Q2) lê parcialmente o Passado (Q0)
    qc_p.measure(2, 2)          # Gravamos a memória do Espião
    
    qc_p.barrier()
    # O FUTURO (T1) - Sem marreta
    qc_p.measure(1, 1)          # Gravamos o Futuro
    qc_p.measure(0, 0)          # Colapso final do Passado

    # ==========================================
    # CIRCUITO ATIVO (A Marreta no Futuro)
    # ==========================================
    qc_a = QuantumCircuit(3, 3)
    qc_a.h(0)
    qc_a.cx(0, 1)
    
    qc_a.barrier()
    # A MEDIÇÃO FRACA (T0)
    qc_a.cry(theta, 0, 2)
    qc_a.measure(2, 2)          # Gravamos a memória do Espião ANTES da marreta
    
    qc_a.barrier()
    # O FUTURO (T1) - A MARRETA
    qc_a.rx(np.pi/2, 1)         # Intervenção agressiva no Futuro (Q1)
    
    qc_a.measure(1, 1)          # Gravamos o Futuro alterado
    qc_a.measure(0, 0)          # Colapso final do Passado

    return [qc_p, qc_a]

circuitos = montar_experimentos_fracos()
circuitos_isa = transpile(circuitos, backend=backend)

SHOTS_POR_LOTE = 4096
NUM_LOTES = 5 
dados_finais = []
sampler = Sampler(backend)

print(f"\n[*] Iniciando extração ({NUM_LOTES} lotes de {SHOTS_POR_LOTE} shots)...")

for lote in range(NUM_LOTES):
    print(f"    -> Lote {lote + 1}/{NUM_LOTES}...")
    try:
        job = sampler.run(circuitos_isa, shots=SHOTS_POR_LOTE)
        result = job.result()
        
        bits_p = result[0].data.c.get_bitstrings()
        bits_a = result[1].data.c.get_bitstrings()
        
        for i in range(SHOTS_POR_LOTE):
            # O Qiskit escreve os bits na ordem: Bit2 Bit1 Bit0
            # Portanto: str[0] é o Espião, str[1] é o Futuro, str[2] é o Passado Forte
            
            str_p = bits_p[i]
            dados_finais.append({
                'Lote': lote, 'Tipo': 'Placebo',
                'Q2_Espiao_T0': int(str_p[0]), 
                'Q1_Futuro_T1': int(str_p[1]),
                'Q0_Forte_Fim': int(str_p[2])
            })
            
            str_a = bits_a[i]
            dados_finais.append({
                'Lote': lote, 'Tipo': 'Ativo',
                'Q2_Espiao_T0': int(str_a[0]), 
                'Q1_Futuro_T1': int(str_a[1]),
                'Q0_Forte_Fim': int(str_a[2])
            })
            
    except Exception as e:
        print(f"    [X] Erro: {e}")

nome_arquivo = f"dataset_janus_medicao_fraca_{backend.name}.csv"
pd.DataFrame(dados_finais).to_csv(nome_arquivo, index=False)
print(f"\n[V] Arquivo {nome_arquivo} gerado com sucesso!")