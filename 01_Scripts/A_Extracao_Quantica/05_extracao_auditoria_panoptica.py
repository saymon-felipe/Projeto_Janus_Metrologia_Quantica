import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
import os
from dotenv import load_dotenv
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

print("\n==========================================================")
print(" 👁️ PROJETO JANUS: AUDITORIA TRIPLA PANÓPTICA (3 Espiões)")
print("==========================================================")

load_dotenv()

TOKEN_IBM = os.getenv("IBM_QUANTUM_TOKEN")

MAQUINA = "ibm_fez"
NUM_LOTES = 5
SHOTS = 4096

try:
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=TOKEN_IBM)
    backend = service.backend(MAQUINA)
    print(f"[*] Conectado. Fila de processamento: {backend.name}")
except Exception as e:
    print(f"[X] Erro: {e}"); exit()

theta = np.pi / 8
n_q = 5 # Q0(Passado), Q1(Futuro), E1, E2, E3

def aplicar_espioes(qc):
    """Aplica o bloco panóptico (3 medições fracas)"""
    qc.barrier()
    qc.cry(theta, 0, 2); qc.measure(2,2)
    qc.cry(theta, 0, 3); qc.measure(3,3)
    qc.cry(theta, 0, 4); qc.measure(4,4)
    qc.barrier()

# ==========================================
# 1. REAL (Corda + Marreta)
# ==========================================
qc_r_p = QuantumCircuit(n_q, n_q); qc_r_p.h(0); qc_r_p.cx(0, 1)
aplicar_espioes(qc_r_p); qc_r_p.measure(1,1); qc_r_p.measure(0,0)

qc_r_a = QuantumCircuit(n_q, n_q); qc_r_a.h(0); qc_r_a.cx(0, 1)
aplicar_espioes(qc_r_a); qc_r_a.rx(np.pi/2, 1); qc_r_a.measure(1,1); qc_r_a.measure(0,0)

# ==========================================
# 2. NULO (Sem Corda + Marreta)
# ==========================================
qc_n_p = QuantumCircuit(n_q, n_q); qc_n_p.h(0); qc_n_p.h(1)
aplicar_espioes(qc_n_p); qc_n_p.measure(1,1); qc_n_p.measure(0,0)

qc_n_a = QuantumCircuit(n_q, n_q); qc_n_a.h(0); qc_n_a.h(1)
aplicar_espioes(qc_n_a); qc_n_a.rx(np.pi/2, 1); qc_n_a.measure(1,1); qc_n_a.measure(0,0)

# ==========================================
# 3. PHANTOM (Corda + Sem Marreta)
# ==========================================
qc_p_p = QuantumCircuit(n_q, n_q); qc_p_p.h(0); qc_p_p.cx(0, 1)
aplicar_espioes(qc_p_p); qc_p_p.measure(1,1); qc_p_p.measure(0,0)

qc_p_a = QuantumCircuit(n_q, n_q); qc_p_a.h(0); qc_p_a.cx(0, 1)
aplicar_espioes(qc_p_a); qc_p_a.measure(1,1); qc_p_a.measure(0,0)

print("[*] Transpilando circuitos (nível 3 para proximidade dos espiões)...")
circuitos_isa = transpile([qc_r_p, qc_r_a, qc_n_p, qc_n_a, qc_p_p, qc_p_a], backend=backend, optimization_level=3)
sampler = Sampler(backend)

arq_real = f"AUDIT_REAL_PANOPTICO_{MAQUINA}.csv"
arq_nulo = f"AUDIT_NULO_PANOPTICO_{MAQUINA}.csv"
arq_phan = f"AUDIT_PHAN_PANOPTICO_{MAQUINA}.csv"

colunas = ['Lote', 'Tipo', 'Q1_Futuro_T1', 'Q0_Forte_Fim', 'Espiao_1', 'Espiao_2', 'Espiao_3']
for arq in [arq_real, arq_nulo, arq_phan]:
    pd.DataFrame(columns=colunas).to_csv(arq, index=False)

print(f"[*] Disparando Auditoria Panóptica em {MAQUINA}...")

for lote in range(NUM_LOTES):
    print(f"    -> Lote {lote+1}/{NUM_LOTES}...")
    try:
        job = sampler.run(circuitos_isa, shots=SHOTS)
        res = job.result()
        bits = [res[i].data.c.get_bitstrings() for i in range(6)]
        
        d_real, d_nulo, d_phan = [], [], []
        
        def ler_linha(lote, tipo, string_bits):
            s = string_bits[::-1] # Corrige a ordem IBM (c0 c1 c2 c3 c4)
            return {
                'Lote': lote, 'Tipo': tipo,
                'Q1_Futuro_T1': int(s[1]), 'Q0_Forte_Fim': int(s[0]),
                'Espiao_1': int(s[2]), 'Espiao_2': int(s[3]), 'Espiao_3': int(s[4])
            }

        for i in range(SHOTS):
            d_real.append(ler_linha(lote, 'Placebo', bits[0][i]))
            d_real.append(ler_linha(lote, 'Ativo',   bits[1][i]))
            d_nulo.append(ler_linha(lote, 'Placebo', bits[2][i]))
            d_nulo.append(ler_linha(lote, 'Ativo',   bits[3][i]))
            d_phan.append(ler_linha(lote, 'Placebo', bits[4][i]))
            d_phan.append(ler_linha(lote, 'Ativo',   bits[5][i]))
            
        pd.DataFrame(d_real).to_csv(arq_real, mode='a', header=False, index=False)
        pd.DataFrame(d_nulo).to_csv(arq_nulo, mode='a', header=False, index=False)
        pd.DataFrame(d_phan).to_csv(arq_phan, mode='a', header=False, index=False)
    except Exception as e:
        print(f"    [X] Erro: {e}"); break

print("\n[V] Arquivos Panópticos gerados com sucesso!")