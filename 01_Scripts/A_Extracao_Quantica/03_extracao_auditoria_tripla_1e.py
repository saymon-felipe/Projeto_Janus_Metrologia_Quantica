import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
import os
from dotenv import load_dotenv
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

print("\n==========================================================")
print(" ⚡ PROJETO JANUS: AUDITORIA FINAL (CORRIGIDA)")
print("==========================================================")

load_dotenv()

TOKEN_IBM = os.getenv("IBM_QUANTUM_TOKEN")

MAQUINA = "ibm_fez"  
NUM_LOTES = 5             # 5 lotes = ~20 mil shots de cada teste.
SHOTS = 4096

try:
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=TOKEN_IBM)
    backend = service.backend(MAQUINA)
    print(f"[*] Conectado. Fila de processamento: {backend.name}")
except Exception as e:
    print(f"[X] Erro: {e}"); exit()

theta = np.pi / 8

# ==========================================
# 1. REAL (Corda + Marreta)
# ==========================================
qc_r_p = QuantumCircuit(3, 3); qc_r_p.h(0); qc_r_p.cx(0, 1); qc_r_p.cry(theta, 0, 2); qc_r_p.measure(2,2); qc_r_p.measure(1,1); qc_r_p.measure(0,0)
qc_r_a = QuantumCircuit(3, 3); qc_r_a.h(0); qc_r_a.cx(0, 1); qc_r_a.cry(theta, 0, 2); qc_r_a.measure(2,2); qc_r_a.rx(np.pi/2, 1); qc_r_a.measure(1,1); qc_r_a.measure(0,0)

# ==========================================
# 2. NULO (Sem Corda + Marreta)
# ==========================================
qc_n_p = QuantumCircuit(3, 3); qc_n_p.h(0); qc_n_p.h(1); qc_n_p.cry(theta, 0, 2); qc_n_p.measure(2,2); qc_n_p.measure(1,1); qc_n_p.measure(0,0)
qc_n_a = QuantumCircuit(3, 3); qc_n_a.h(0); qc_n_a.h(1); qc_n_a.cry(theta, 0, 2); qc_n_a.measure(2,2); qc_n_a.rx(np.pi/2, 1); qc_n_a.measure(1,1); qc_n_a.measure(0,0)

# ==========================================
# 3. PHANTOM (Corda + Sem Marreta)
# ==========================================
qc_p_p = QuantumCircuit(3, 3); qc_p_p.h(0); qc_p_p.cx(0, 1); qc_p_p.cry(theta, 0, 2); qc_p_p.measure(2,2); qc_p_p.measure(1,1); qc_p_p.measure(0,0)
qc_p_a = QuantumCircuit(3, 3); qc_p_a.h(0); qc_p_a.cx(0, 1); qc_p_a.cry(theta, 0, 2); qc_p_a.measure(2,2); qc_p_a.measure(1,1); qc_p_a.measure(0,0)

circuitos_isa = transpile([qc_r_p, qc_r_a, qc_n_p, qc_n_a, qc_p_p, qc_p_a], backend=backend)
sampler = Sampler(backend)

arq_real = f"AUDIT_REAL_{MAQUINA}.csv"
arq_nulo = f"AUDIT_NULO_{MAQUINA}.csv"
arq_phan = f"AUDIT_PHAN_{MAQUINA}.csv"

for arq in [arq_real, arq_nulo, arq_phan]:
    pd.DataFrame(columns=['Lote', 'Tipo', 'Q2_Espiao_T0', 'Q1_Futuro_T1', 'Q0_Forte_Fim']).to_csv(arq, index=False)

print(f"[*] Disparando Auditoria Tripla em {MAQUINA}...")

for lote in range(NUM_LOTES):
    print(f"    -> Lote {lote+1}/{NUM_LOTES}...")
    try:
        job = sampler.run(circuitos_isa, shots=SHOTS)
        res = job.result()
        bits = [res[i].data.c.get_bitstrings() for i in range(6)]
        
        d_real, d_nulo, d_phan = [], [], []
        
        for i in range(SHOTS):
            d_real.append({'Lote': lote, 'Tipo': 'Placebo', 'Q2_Espiao_T0': int(bits[0][i][0]), 'Q1_Futuro_T1': int(bits[0][i][1]), 'Q0_Forte_Fim': int(bits[0][i][2])})
            d_real.append({'Lote': lote, 'Tipo': 'Ativo',   'Q2_Espiao_T0': int(bits[1][i][0]), 'Q1_Futuro_T1': int(bits[1][i][1]), 'Q0_Forte_Fim': int(bits[1][i][2])})
            
            d_nulo.append({'Lote': lote, 'Tipo': 'Placebo', 'Q2_Espiao_T0': int(bits[2][i][0]), 'Q1_Futuro_T1': int(bits[2][i][1]), 'Q0_Forte_Fim': int(bits[2][i][2])})
            d_nulo.append({'Lote': lote, 'Tipo': 'Ativo',   'Q2_Espiao_T0': int(bits[3][i][0]), 'Q1_Futuro_T1': int(bits[3][i][1]), 'Q0_Forte_Fim': int(bits[3][i][2])})
            
            d_phan.append({'Lote': lote, 'Tipo': 'Placebo', 'Q2_Espiao_T0': int(bits[4][i][0]), 'Q1_Futuro_T1': int(bits[4][i][1]), 'Q0_Forte_Fim': int(bits[4][i][2])})
            d_phan.append({'Lote': lote, 'Tipo': 'Ativo',   'Q2_Espiao_T0': int(bits[5][i][0]), 'Q1_Futuro_T1': int(bits[5][i][1]), 'Q0_Forte_Fim': int(bits[5][i][2])})
            
        pd.DataFrame(d_real).to_csv(arq_real, mode='a', header=False, index=False)
        pd.DataFrame(d_nulo).to_csv(arq_nulo, mode='a', header=False, index=False)
        pd.DataFrame(d_phan).to_csv(arq_phan, mode='a', header=False, index=False)
    except Exception as e:
        print(f"    [X] Erro ou Fim do Tempo: {e}"); break

print("\n[V] Arquivos gerados com sucesso!")