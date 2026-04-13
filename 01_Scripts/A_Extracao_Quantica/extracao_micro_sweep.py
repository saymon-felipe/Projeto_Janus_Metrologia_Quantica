import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
import os
from dotenv import load_dotenv
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

print("\n==========================================================")
print(" 🎯 PROJETO JANUS: MICRO-VARREDURA OTIMIZADA PARA CNN")
print("==========================================================")

load_dotenv()

TOKEN_IBM = os.getenv("IBM_QUANTUM_TOKEN")

NOME_DA_MAQUINA = "ibm_fez"

try:
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=TOKEN_IBM)
    backend = service.backend(NOME_DA_MAQUINA)
    print(f"[*] Conectado a {backend.name}. Preparando a extração cirúrgica...")
except Exception as e:
    print(f"[X] Erro Crítico: {e}")
    exit()

# Matriz fixa em 40 (120 qubits), micro-ajuste no ângulo
ANGULOS = [np.pi/9, np.pi/8, np.pi/7]
NUM_PARES = 40
SHOTS = 4000

def criar_circuito(theta, ativo=False):
    total_q = NUM_PARES * 3
    qc = QuantumCircuit(total_q, total_q)
    for i in range(NUM_PARES):
        q0, q1, q2 = i*3, i*3+1, i*3+2
        
        # O Túnel no Tempo
        qc.h(q0)
        qc.cx(q0, q1)
        
        # A Medição Fraca
        qc.cry(theta, q0, q2)
        qc.measure(q2, q2)
        
        # A Marreta
        if ativo:
            qc.rx(np.pi/2, q1)
            
        qc.measure(q1, q1)
        qc.measure(q0, q0)
    return qc

circuitos_para_rodar = []
metadados = []

print("[*] A construir 6 circuitos de alta densidade...")
for angulo in ANGULOS:
    circuitos_para_rodar.append(criar_circuito(angulo, ativo=False))
    metadados.append({'Angulo': angulo, 'Tipo': 'Placebo'})
    
    circuitos_para_rodar.append(criar_circuito(angulo, ativo=True))
    metadados.append({'Angulo': angulo, 'Tipo': 'Ativo'})

print("[*] Transpilando (Nível 3 - Otimização máxima de Crosstalk)...")
circuitos_isa = transpile(circuitos_para_rodar, backend=backend, optimization_level=3)

print(f"[*] A ENVIAR JOB PARA A IBM ({SHOTS} disparos por circuito)...")
sampler = Sampler(backend)
try:
    job = sampler.run(circuitos_isa, shots=SHOTS)
    print(f"    [V] Job submetido com sucesso! ID: {job.job_id()}")
    
    print("[*] A aguardar execução...")
    result = job.result()
    
    dados_varredura = []
    
    for idx, pub_result in enumerate(result):
        meta = metadados[idx]
        bits = pub_result.data.c.get_bitstrings()
        
        for shot_idx, string_bits in enumerate(bits):
            str_invertida = string_bits[::-1]
            
            for par in range(NUM_PARES):
                idx0, idx1, idx2 = par*3, par*3+1, par*3+2
                dados_varredura.append({
                    'Angulo_Rad': round(meta['Angulo'], 4),
                    'Shot': shot_idx,
                    'ID_Par': par,
                    'Tipo': meta['Tipo'],
                    'Q2_Espiao_T0': int(str_invertida[idx2]), 
                    'Q1_Futuro_T1': int(str_invertida[idx1]),
                    'Q0_Forte_Fim': int(str_invertida[idx0])
                })
                
    nome_arquivo = "dataset_micro_sweep_cnn.csv"
    pd.DataFrame(dados_varredura).to_csv(nome_arquivo, index=False)
    print(f"\n[V] SUCESSO! {len(dados_varredura)} linhas extraídas para {nome_arquivo}.")

except Exception as e:
    print(f"\n[X] Erro de execução: {e}")