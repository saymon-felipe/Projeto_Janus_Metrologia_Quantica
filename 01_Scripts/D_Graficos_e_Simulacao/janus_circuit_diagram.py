# janus_circuit_diagram.py
from qiskit import QuantumCircuit
import matplotlib.pyplot as plt

def renderizar_arquitetura_janus():
    qc = QuantumCircuit(3, 1)
    
    # Preenchimento do Circuito
    qc.h(0)            # Q0 (Forte): Cria a incerteza do Passado
    qc.cx(0, 1)        # Emaranhamento Q0-Q1 (A Corda)
    qc.barrier(label="T_0 (Passado)")
    
    # O Espião (Medição Fraca)
    qc.cry(3.14159/8, 0, 2) # Ponto mágico de pi/8
    qc.barrier(label="T_1 (Futuro)")
    
    # A Marreta (Intervenção)
    qc.rx(3.14159/2, 1) 
    
    # Pós-Seleção
    qc.measure(1, 0)
    
    fig = qc.draw(output='mpl', style='clifford')
    fig.savefig("janus_arquitetura_circuito.png", dpi=300, bbox_inches="tight")
    print("[*] Topologia do Modelo Janus exportada (janus_arquitetura_circuito.png).")

if __name__ == "__main__":
    renderizar_arquitetura_janus()