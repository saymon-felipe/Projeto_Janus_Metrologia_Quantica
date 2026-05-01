import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
import os
from dotenv import load_dotenv
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

load_dotenv()
token_ibm = os.getenv("IBM_QUANTUM_TOKEN")
maquina_ibm = "ibm_marrakesh"
theta_espiao = np.pi / 8
total_qubits = 5
shots_por_bit = 2048

servico = QiskitRuntimeService(channel="ibm_quantum_platform", token=token_ibm)
backend_ibm = servico.backend(maquina_ibm)

ALFABETO = " ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def char_para_5bit(char):
    idx = ALFABETO.find(char.upper())
    if idx == -1: idx = 0 
    return format(idx, '05b')

def codificar_hamming_9_5(bits_5):
    d = [int(x) for x in bits_5]
    p1 = d[0] ^ d[1] ^ d[3] ^ d[4]
    p2 = d[0] ^ d[2] ^ d[3]
    p4 = d[1] ^ d[2] ^ d[3]
    p8 = d[4]
    return f"{p1}{p2}{d[0]}{p4}{d[1]}{d[2]}{d[3]}{p8}{d[4]}"

def aplicar_interleaving(blocos_9bits):
    resultado = ""
    for bit_idx in range(9):
        for bloco in blocos_9bits:
            resultado += bloco[bit_idx]
    return resultado

mensagem_texto = "STEINSGATE"

bits_base = [char_para_5bit(c) for c in mensagem_texto]
blocos_hamming = [codificar_hamming_9_5(b) for b in bits_base]
payload_interleaved = aplicar_interleaving(blocos_hamming)

cabecalho_calibracao = "0101"
sequencia_completa = cabecalho_calibracao + payload_interleaved

def construir_circuito_bit(valor_bit):
    circuito = QuantumCircuit(total_qubits, total_qubits)
    
    circuito.h(0)
    # ---------------------------------------------------------
    # TESTE DE CONTROLE: CNOT REMOVIDO
    # circuito.cx(0, 1) 
    # O Qubit 0 (Passado) e o Qubit 1 (Futuro) não estão mais conectados.
    # ---------------------------------------------------------
    
    circuito.barrier()
    circuito.cry(theta_espiao, 0, 2)
    circuito.measure(2, 2)
    circuito.cry(theta_espiao, 0, 3)
    circuito.measure(3, 3)
    circuito.cry(theta_espiao, 0, 4)
    circuito.measure(4, 4)
    circuito.barrier()
    
    if valor_bit == '1':
        # A marreta bate no futuro, mas o alvo está isolado no espaço-tempo.
        circuito.rx(np.pi/2, 1)
        
    circuito.measure(1, 1)
    circuito.measure(0, 0)
    return circuito

lista_circuitos = [construir_circuito_bit(b) for b in sequencia_completa]
circuitos_compilados = transpile(lista_circuitos, backend=backend_ibm, optimization_level=3)

amostrador = Sampler(backend_ibm)
arquivo_saida = "janus_sinal_v8_controle.csv"
colunas = ['ordem_sequencia', 'q1_futuro', 'q0_passado', 'espiao_1', 'espiao_2', 'espiao_3']
pd.DataFrame(columns=colunas).to_csv(arquivo_saida, index=False)

print("[*] Disparando Teste de Controle (Sem Emaranhamento)...")
try:
    tarefa = amostrador.run(circuitos_compilados, shots=shots_por_bit)
    resultado_tarefa = tarefa.result()
    
    for ordem_idx, resultado_circ in enumerate(resultado_tarefa):
        dados_bit = []
        bits_medidos = resultado_circ.data.c.get_bitstrings()
        for string_bin in bits_medidos:
            str_inv = string_bin[::-1]
            dados_bit.append({
                'ordem_sequencia': ordem_idx, 'q1_futuro': int(str_inv[1]),
                'q0_passado': int(str_inv[0]), 'espiao_1': int(str_inv[2]),
                'espiao_2': int(str_inv[3]), 'espiao_3': int(str_inv[4])
            })
        pd.DataFrame(dados_bit).to_csv(arquivo_saida, mode='a', header=False, index=False)
    print("\n[V] Transmissão de Controle concluída.")
except Exception as e:
    print(f"\n[X] Falha na transmissão: {e}")