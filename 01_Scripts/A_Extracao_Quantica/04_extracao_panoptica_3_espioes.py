import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
import os
from dotenv import load_dotenv
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

print("\n==========================================================")
print(" 👁️ PROJETO JANUS: OPERAÇÃO PANÓPTICO (Múltiplos Espiões)")
print("==========================================================")

load_dotenv()

TOKEN_IBM = os.getenv("IBM_QUANTUM_TOKEN")

try:
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=TOKEN_IBM)
    NOME_DA_MAQUINA = "ibm_fez" 
    backend = service.backend(NOME_DA_MAQUINA)
    print(f"[*] Conectado ao Hardware: {backend.name}")
except Exception as e:
    print(f"[X] Erro Crítico: {e}")
    exit()

NUM_ESPIOES = 3
THETA = np.pi / 8

def criar_circuito_panoptico(ativo=False):
    total_q = 2 + NUM_ESPIOES # Q0(Passado), Q1(Futuro), Q2(E1), Q3(E2), Q4(E3)
    qc = QuantumCircuit(total_q, total_q)
    
    # 1. Entrelaçamento Original
    qc.h(0)
    qc.cx(0, 1)
    qc.barrier()
    
    # 2. A Sequência de Espiões (Múltiplas Medições Fracas em T0)
    for i in range(NUM_ESPIOES):
        q_espiao = i + 2
        qc.cry(THETA, 0, q_espiao)
        qc.measure(q_espiao, q_espiao)
        
    qc.barrier()
    
    # 3. O Futuro (T1)
    if ativo:
        qc.rx(np.pi/2, 1) # A Marreta
        
    qc.measure(1, 1)
    qc.measure(0, 0)
    
    return qc

print("[*] Construindo os circuitos do Panóptico...")
circ_placebo = criar_circuito_panoptico(ativo=False)
circ_ativo = criar_circuito_panoptico(ativo=True)

print("[*] Transpilando para a topologia do chip...")
circuitos_isa = transpile([circ_placebo, circ_ativo], backend=backend, optimization_level=3)

SHOTS = 10000
sampler = Sampler(backend)

print(f"[*] A DISPARAR! Pedindo {SHOTS} matrizes de consenso...")
try:
    job = sampler.run(circuitos_isa, shots=SHOTS)
    print(f"    [V] Job submetido! ID: {job.job_id()}")
    
    print("[*] A aguardar a IBM...")
    result = job.result()
    
    dados_finais = []
    
    for idx, pub_result in enumerate(result):
        tipo = 'Placebo' if idx == 0 else 'Ativo'
        bits = pub_result.data.c.get_bitstrings()
        
        for shot_idx, string_bits in enumerate(bits):
            # A Qiskit devolve a string invertida: c4 c3 c2 c1 c0
            str_invertida = string_bits[::-1] 
            
            dados_finais.append({
                'Shot': shot_idx,
                'Tipo': tipo,
                'Q0_Passado_Forte': int(str_invertida[0]),
                'Q1_Futuro_T1': int(str_invertida[1]),
                'Espiao_1': int(str_invertida[2]),
                'Espiao_2': int(str_invertida[3]),
                'Espiao_3': int(str_invertida[4])
            })
            
    nome_arquivo = f"dataset_panoptico_{backend.name}.csv"
    pd.DataFrame(dados_finais).to_csv(nome_arquivo, index=False)
    print(f"\n[V] SUCESSO! {len(dados_finais)} eventos gravados em {nome_arquivo}.")

except Exception as e:
    print(f"\n[X] Erro de execução: {e}")