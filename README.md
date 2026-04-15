# **Metrologia Temporal de Precisão em Sistemas NISQ: Detecção de Modulação Retrocausal Estocástica via Consenso Panóptico**

**Status:** Publicado (Preprint) | Sinal Validado ($5\sigma$)

**Hardware Alvo:** Ecossistema IBM Quantum Heron r2 (156 Qubits)

**Tecnologias Principais:** Qiskit, Python, AI Signature Extraction (Random Forest)

## **📌 Visão Geral**

O protocolo aqui descrito foca-se numa metodologia avançada de metrologia temporal aplicada a processadores quânticos de escala intermediária ruidosa (NISQ). A pesquisa fundamenta-se no **Formalismo de Vetores de Dois Estados (TSVF)**, utilizando medições fracas sequenciais para detetar correlações estatísticas anómalas entre o passado ($t_0$) e o futuro ($t_1$) de sistemas entrelaçados.

A implementação utiliza uma arquitetura de "Consenso Panóptico", onde múltiplos sensores quânticos realizam extrações parciais de informação da função de onda. Através de algoritmos de Machine Learning, o protocolo identifica assinaturas estruturais no ruído de fundo do chip Heron r2, permitindo a deteção destas correlações com alta precisão e rigor estatístico.

## **📊 Resultados de Eficácia (Hardware Real)**

Em testes rigorosos operados na arquitetura **IBM Heron r2** (processadores ibm\_kingston, ibm\_fez e ibm\_marrakesh), o protocolo isolou a modulação retrocausal com os seguintes marcos:

* **Precisão Máxima:** 71.55% (Hardware Kingston)  
* **Significância Estatística:** $5\sigma$ ($p$\-value \< $10^{-6}$)  
* **Área Sob a Curva (AUC):** 0.679  
* **Integridade Causal:** Testes de "Massa Bruta" e "Fantasma" estabilizaram em \~51.80%, provando total respeito ao Teorema da Não-Comunicação.

\<p align="center"\>

\<img src="04\_Assets\_Visuais/janus\_distribuicao\_retrocausal.jpg" alt="Distribuição Retrocausal" width="800"/\>

\<em\>Figura: Distribuição de densidade e entropia revelando o deslocamento do sinal retrocausal face ao ruído fantasma.</em\>

\</p\>

## **📂 Estrutura do Repositório**

O projeto está organizado metodicamente para garantir a replicabilidade e a transparência da auditoria de dados:

* **01\_Scripts/**: Motores de extração quântica (Qiskit) e pipelines de análise via Random Forest.  
* **02\_Datasets\_Brutos/**: Telemetria original extraída dos processadores IBM Heron r2 (156 qubits).  
* **03\_Resultados\_Validados/**: Dossiês de laboratório consolidando os resultados de precisão e validade estatística.  
* **04\_Assets\_Visuais/**: Matrizes de Confusão, Curvas ROC e diagramas topológicos.

## **🚀 Guia de Replicação Técnica**

Para validar o protocolo empiricamente em hardware real, deve-se seguir a sequência estrita de auditoria:

### **1\. Extração Panóptica**

O script cria o circuito e realiza medições fracas acopladas (com ângulo $\theta = \pi/8$) em qubits entrelaçados. Esta redundância é crítica para mitigar o ruído térmico da arquitetura Heron e criar uma matriz de consenso.

python 01\_Scripts/A\_Extracao\_Quantica/05\_extracao\_auditoria\_panoptica.py

### **2\. Análise via Pós-Seleção de Aharonov**

A inteligência artificial processa o dataset bruto aplicando o filtro de pós-seleção: apenas os estados onde a medição futura ($t_1$) colapsou em $|1\rangle$ são retidos. O modelo (Random Forest) é então treinado para distinguir o cenário ativo do placebo analisando *exclusivamente* as matrizes de dados extraídas no passado.

python 01\_Scripts/B\_Analise\_Estatistica\_IA/05\_analise\_auditoria\_panoptica.py

### **3\. Validação de Integridade Causal (Massa Bruta)**

Como teste de controlo rigoroso contra falsos positivos, a análise preditiva é repetida sem o filtro de pós-seleção condicionado. Em total conformidade com o Teorema do Não-Sinal (No-Signaling Theorem) da mecânica quântica, a precisão do modelo deve obrigatoriamente colapsar para o limiar de aleatoriedade (\~50%). Isso confirma a ausência de viés clássico ou erro sistemático de leitura no chip.

python 01\_Scripts/B\_Analise\_Estatistica\_IA/06\_analise\_integridade\_causal\_massa\_bruta.py

## **🧠 Assinatura de Importância: O que a IA deteta?**

A extração de sinal operada pelo Protocolo D-Janus não se baseia em leitura direta de bits, mas no reconhecimento de padrões não-lineares em três métricas fundamentais do ruído quântico:

1. **Taxa de Mudança (Flicker):** Variável de maior peso preditivo (\>45%). Reflete o amortecimento estrutural das oscilações de fase no passado induzidas retroativamente pela intervenção no futuro.  
2. **Entropia de Shannon Local:** Mede a estabilização da desordem estatística no consenso dos sensores quânticos acoplados.  
3. **Densidade de Probabilidade de Viés:** Monitora o sutil deslocamento da amplitude captada de forma não-destrutiva pelas medições fracas em $t_0$.

## **📖 Como Citar este Trabalho (Citation)**

Se utilizar o Protocolo D-Janus, os scripts de Consenso Panóptico ou os datasets brutos na sua pesquisa, por favor, cite a publicação oficial:

@misc{delima\_janus\_2026,  
  author       \= {de Lima, Saymon Felipe and Gemini},  
  title        \= {Metrologia Temporal de Precisão em Sistemas NISQ: Detecção de Modulação Retrocausal Estocástica via Consenso Panóptico},  
  month        \= apr,  
  year         \= 2026,  
  publisher    \= {Zenodo},  
  doi          \= {10.5281/zenodo.19583315},  
  url          \= {\[https://doi.org/10.5281/zenodo.19583315\](https://doi.org/10.5281/zenodo.19583315)}  
}

*Documentação gerada para fins de registo de pesquisa metodológica e auditoria em arquiteturas NISQ pela KSI \- Kinetic Solutions.*