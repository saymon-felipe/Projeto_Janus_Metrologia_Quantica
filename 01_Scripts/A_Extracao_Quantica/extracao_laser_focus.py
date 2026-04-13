import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
import os
from dotenv import load_dotenv
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

print("\n==========================================================")
print(" ⚡ PROJETO JANUS: EXTRAÇÃO 'LASER FOCUS' (< 8 SEGUNDOS)")
print("==========================================================")

load_dotenv()

TOKEN_IBM = os.getenv("IBM_QUANTUM_TOKEN")

NOME_DA_MAQUINA = "ibm_fez"

try:
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=TOKEN_IBM)
    backend = service.backend(NOME_DA_MAQUINA)
    print(f"[*] Conectado a {backend.name}. Alvo fixado.")
except Exception as e:
    print(f"[X] Erro Crítico: {e}")
    exit()

ANGULO_VENCEDOR = np.pi / 9  # 0.3491 Radianos
NUM_PARES = 40               # Matriz completa (120 qubits)
SHOTS_MASSIVOS = 10000       # 10.000 Placebos + 10.000 Ativos

def criar_circuito(theta, ativo=False):
    total_q = NUM_PARES * 3
    qc = QuantumCircuit(total_q, total_q)
    for i in range(NUM_PARES):
        q0, q1, q2 = i*3, i*3+1, i*3+2
        qc.h(q0)
        qc.cx(q0, q1)
        qc.cry(theta, q0, q2)
        qc.measure(q2, q2)
        if ativo:
            qc.rx(np.pi/2, q1)
        qc.measure(q1, q1)
        qc.measure(q0, q0)
    return qc

print("[*] Construindo os únicos 2 circuitos...")
circ_placebo = criar_circuito(ANGULO_VENCEDOR, ativo=False)
circ_ativo = criar_circuito(ANGULO_VENCEDOR, ativo=True)

print("[*] Transpilando (Nível 3) para a topologia Eagle...")
circuitos_isa = transpile([circ_placebo, circ_ativo], backend=backend, optimization_level=3)

print(f"[*] A DISPARAR! Pedindo {SHOTS_MASSIVOS * 2} matrizes no total...")
sampler = Sampler(backend)

try:
    job = sampler.run(circuitos_isa, shots=SHOTS_MASSIVOS)
    print(f"    [V] Submetido! ID: {job.job_id()}")
    
    print("[*] A aguardar a IBM...")
    result = job.result()
    
    dados_finais = []
    
    for idx, pub_result in enumerate(result):
        tipo = 'Placebo' if idx == 0 else 'Ativo'
        bits = pub_result.data.c.get_bitstrings()
        
        for shot_idx, string_bits in enumerate(bits):
            str_invertida = string_bits[::-1]
            for par in range(NUM_PARES):
                idx0, idx1, idx2 = par*3, par*3+1, par*3+2
                dados_finais.append({
                    'Shot': shot_idx,
                    'ID_Par': par,
                    'Tipo': tipo,
                    'Q2_Espiao_T0': int(str_invertida[idx2]), 
                    'Q1_Futuro_T1': int(str_invertida[idx1]),
                    'Q0_Forte_Fim': int(str_invertida[idx0])
                })
                
    nome_arquivo = "dataset_laser_focus_cnn.csv"
    pd.DataFrame(dados_finais).to_csv(nome_arquivo, index=False)
    print(f"\n[V] DADOS SALVOS! Extraídas {len(dados_finais)} medições para {nome_arquivo}.")

except Exception as e:
    print(f"\n[X] Erro de execução: {e}")