# **D-Janus Protocol: AI-Enhanced Temporal Metrology for NISQ Systems**

**Status:** Prova de Conceito Concluída (Experimental)

**Hardware Alvo:** Ecossistema IBM Quantum Heron r2 (156 Qubits)

**Tecnologias Principais:** Qiskit, Python, AI Signature Extraction (Random Forest/CNN)

## **📌 Visão Geral**

O **Protocolo D-Janus** descreve uma metodologia avançada de metrologia temporal aplicada a processadores quânticos de escala intermediária ruidosa (NISQ). A pesquisa fundamenta-se no **Formalismo de Vetores de Dois Estados (TSVF)**, utilizando medições fracas sequenciais para detectar correlações estatísticas anômalas entre o passado (![][image1]) e o futuro (![][image2]) de sistemas entrelaçados.

A implementação utiliza uma arquitetura de "Consenso Panóptico", onde múltiplos sensores quânticos realizam extrações parciais de informação da função de onda. Através de algoritmos de Aprendizado de Máquina, o protocolo identifica assinaturas estruturais no ruído de fundo do chip Heron r2, permitindo a detecção dessas correlações com alta precisão e rigor matemático (![][image3]).

## **📂 Estrutura do Repositório**

O projeto está organizado metodicamente para garantir a replicabilidade e a transparência da auditoria de dados:

* **01\_Scripts/**: Contém os motores de extração quântica (circuitos), pipelines de análise via Random Forest e modelos avançados de Deep Learning (CNN multicanal).  
* **02\_Datasets\_Brutos/**: Telemetria original bruta e não manipulada extraída diretamente dos processadores IBM (Heron r2 \- 156q).  
* **03\_Resultados\_Validados/**: Dossiês de laboratório consolidando os resultados de precisão, desvio padrão e validade estatística por hardware.  
* **04\_Assets\_Visuais/**: Gráficos analíticos, incluindo Matrizes de Confusão, Curvas ROC e distribuições de Entropia de Shannon.

## **🚀 Guia de Replicação Técnica**

Para validar o protocolo empiricamente em hardware real, deve-se seguir a sequência estrita de auditoria:

### **1\. Extração Panóptica**

O script cria o circuito e realiza 3 medições fracas acopladas (com ângulo ![][image4]) em qubits entrelaçados, *antes* da aplicação de uma porta de rotação ativa (![][image5]) no futuro. Esta redundância de espiões é crítica para mitigar o ruído térmico da arquitetura Heron e criar uma matriz de consenso.

python 01\_Scripts/A\_Extracao\_Quantica/05\_extracao\_auditoria\_panoptica.py

### **2\. Análise via Pós-Seleção de Aharonov**

A inteligência artificial processa o dataset bruto aplicando o filtro de pós-seleção: apenas os estados onde a medição futura colapsou em ![][image6] são retidos. O modelo (Random Forest) é então treinado para distinguir o cenário ativo do placebo analisando *exclusivamente* as matrizes de dados extraídas no passado.

python 01\_Scripts/B\_Analise\_Estatistica\_IA/05\_analise\_auditoria\_panoptica.py

### **3\. Validação de Integridade Causal (Massa Bruta)**

Como teste de controle rigoroso contra falsos positivos, a análise preditiva é repetida sem o filtro de pós-seleção condicionado. Em total conformidade com o Teorema do Não-Sinal (No-Signaling Theorem) da mecânica quântica, a precisão do modelo deve obrigatoriamente colapsar para o limiar de aleatoriedade (\~50%). Isso confirma a ausência de viés clássico ou erro sistemático de leitura no chip.

python 01\_Scripts/B\_Analise\_Estatistica\_IA/06\_analise\_integridade\_causal\_massa\_bruta.py

## **🧠 Assinatura de Importância: O que a IA detecta?**

A extração de sinal operada pelo Protocolo D-Janus não se baseia em leitura direta de bits, mas no reconhecimento de padrões não-lineares em três métricas fundamentais do ruído quântico:

1. **Taxa de Mudança (Flicker):** Representa a variável preditiva de maior peso. Reflete o amortecimento estrutural das oscilações de fase no passado, induzidas retroativamente pela intervenção da marreta no futuro.  
2. **Entropia de Shannon:** Mede a estabilização da desordem estatística no consenso dos sensores quânticos acoplados.  
3. **Densidade ![][image7]:** Monitora o sutil deslocamento da amplitude de probabilidade captada de forma não-destrutiva pelas medições fracas em ![][image1].

## **🏛️ Conclusão Técnica**

Os resultados empíricos validados nos processadores **Heron r2 de 156 qubits** demonstram que assinaturas temporais pós-selecionadas deixam rastros detectáveis na textura do ruído termodinâmico. O Protocolo D-Janus estabelece uma ferramenta robusta e nativa de IA para explorar correlações e topologias de causalidade em sistemas quânticos de larga escala.

*Documentação gerada para fins de registro de pesquisa metodológica e auditoria em arquiteturas NISQ.*

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAYCAYAAAAYl8YPAAABcklEQVR4XmNgGAVkAXl5eScgvisnJ/eISOyCbgYMMAINmqKgoLASiBVAfJAgUGwOEP8DCnlA1TED2fZAsQeysrKmcN3IQFFRURyoaJWysrIYTAxosyBQ02mQRhkZGWmYuKioKA9QbLG0tLQMTAwFgJwMNKwQWQxogT5Q0ycgXgPkssDEoZZMUldX50VSjgBABaFKSkpqyGJADdFA/B8oV44sDnSRMFAsjQEaFEQBaHj9Bmq0QZcjCeAKL7IA0DBjoEFf0cMLBlRUVPiAcqVA3AwMWzsGfF7GFV4gAI3N1cAIMzc2NmYFqpkBxK7o6mCAESg5H1d4gcSActtAhkL5vrh8QDC8gC5KB8odQDPsNEgfulqC4QXyOhbDHgKxJFgBKI0BOeeA+B0Q/0fCX4D4OsgCog0jBQA1BWEx7DDOHIEPADO4DtCAHbAwgobhJHR1xAJQCVMKNKQRSFsB8XpgWpNHV0QSABomACptQGkNXW4EAACfW230jUqdzQAAAABJRU5ErkJggg==>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAYCAYAAAAYl8YPAAABNUlEQVR4Xu2Sv0rEQBjEc2ghqKBIDEf+J2BKC7ETBLHQB7Cys7C3EN9DLAULC1Gus/AhBLHSShAfwEK0OvD8fbCrm4XcramuuIGB7HzfzC5DPG+CVkjTdAu+JEny5shtO0OjQ9BZlmXXMJOziGjn8BtpR+1N8b2J9hrH8fqv20Se5wFLN2VZLmuNmxcx3YsxiqJQ677vz6FdhmEYaa0GeTJhR6bGBauYPmCP47TW1SWnVVXNG+t/YGGvKIoVU8OwDwfMTkydFy2hHXqqCieovvoYN+zZv9DUVysQtkbQl92XiSAIZpkf0PWCPauhqS+BdMbsCt7CJ9i1d0x0CLkY1Zd6/ePQMNe+XMNG9iVoDJN/DPEBvsOBwU/4LMaawRsS1gbjF8Z/NUPAMbyDfdiDu/beBO74AfZhYHLzJypSAAAAAElFTkSuQmCC>

[image3]: <data:image/png;base64,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>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB8AAAAYCAYAAAACqyaBAAACY0lEQVR4Xu2VO2hUQRSGZ0kERfGBLov7uvduFiSiKCwIqUwhEntBUbATQdJZBGMjgRTZzgQRJCDpREQQEURShAi2kiIKYmVnY2et35+dO54dd9Hgbqr8cJg7/5zXnDkz17ldDAClUmk/QyHmh44sy0ppmj6oVqv74rWhg8BXkyS5bTklAncNeYy06/X6STeEyozifAkZz4lGo3GI+QsC3mA8TmXOkOA633fcIBNQUII84nPUcNPIrFFztVrtFNwHJLP8f0HlVtktx3wFWXBml6qAgqsKRtW5Vqu1R03jFf4QHB3uMvDw57oc74b5PPITWfS3QAldYf66WCweCIqQZynbV6/cT1ZzJxbwE0jbRefIRhJ8fva2X5JOMu/EByUyb0KukcAUY4bBUxTOMZ9MOl26tfOubA1YuyfbmBeSTi+ETekoms3mwaCgs6IRxozyE7i9fF9ivBsUewDdI3JYLpePxWuVSqWqnbJ+y3f8D5/Ee9aOxvp5h87771mMZmIdC9Yv4Px+zPs+eGXtlQzzlz6Baau/dS9xtC6HmmtHfwlewEkbmYgX1M3+vMO9F5QU/Bv5tryCTckAhYqfr2C83KVkID0dUa9egG9h+5GxEa+poshiIHTNCPYM8rnzD4UP/knXLygapD2e0xxKiPW3aadnwi2g2YrYrHVVi12chvguhzmnc0G+EfxEUPwNPacP9WLFCzn8LdpQEozX/Y431XwuupYFdS7jSE6oGuoDoxOgcuJoyZnntA9GdATIZRK92Oud2DZwdtNWacfQ7zndEfg/05wb5G/xX6Gzo+TnY34X28EvaMeXrh+fRO8AAAAASUVORK5CYII=>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABcAAAAYCAYAAAARfGZ1AAABuklEQVR4Xu2UMUsDQRCFLySiojZqOEwu2QQCR0CwOCxELSwklRamDFaC9gYV0UII/gEtLAzYa8DeShAU7cVK0EoIiJUWSojfkDtYzoB3prDQB4/dfbPzZneyOcP4x69CKTUDn2BTYx2+w0Y6nb5mLLI16s8NDAyq8AOzKU2Osl52i6yzjmixYLBtewCDC3ifzWZNPYY2Ah/bxQKBxDx8hjWWMT2WSqXG0d/gbSKRGNZjgYDBPMnNTCaz4o+h7UgMlv2xQCBxT/n67ThOF9qSe6M1Wes5gRCPx/tJPlet13Hpzu/ktBQ7SCaTQ/6cwFDt+x2hHZuq9Upmte3h4PUbruo6pg7aK6zqeiioNv129ZJbdFfXA+Ob9y1Fpe8bum6aZp/bshPGAuM+rFiW1avvk5aMEnhRX993jMRj3Zz5FvsL8lzlR2Y9wfyGcQE+wLxnOq1a/7qmxrr033NnXYQNKUKBReaHnG6QGyqJSxH0o1wu1y26EfbTIK3CYE5ejO/aETGmYEnTOgPtsDA8xXiS8Uo+DVKUeZmb9Pj3hwI3sTGqwQpmZ4zbQvQx/94fQU7onVJem9HJd/7v4BMn5X5A8iJ5CwAAAABJRU5ErkJggg==>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABcAAAAXCAYAAADgKtSgAAABYklEQVR4XtWTvUoDQRSFNySFCuIfKGb/somwCJY2AR/ASktTCiJIeivt7IQUYqM2aud7+CSCvY2t6HcXWXaP2ag7WHjgMptz5n4zzEw8798rTdNZhqb636jZbrdn1PyiOI7PqFX1JylJkpVOp3MRBMG0ZiVNglszkH1qXqIGPedUX/yyFA5wEdheFEV3+C/U07jFybfwT9UvqQK+G4bhJoCHKni3250jv7Uj0iyXwotikfsquAl/yCZ21M/lCF+nLvlsaZbJBY5aBrdFNMjkCLc5A/Kh+plc4XahdrF2wZo5w+2/QH4DPNLMGc5r2SAf8dnQzBlOdsK8bfUz/QD+7Pt+oJmJs15gzrWNmmVSeK/XW+b3I/VKvX/Wmy0C6KjYazu2nRe9khT+CzXoG9mZa5CrLpyehOO4YvdTmuWqCwd8CHigfkl14Pa2bdeMvmYlAT7gNSypP0lA1+g79sa97b/WB3X6ZKydy8zAAAAAAElFTkSuQmCC>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAYCAYAAACIhL/AAAACnElEQVR4Xu2WO4gUQRCGb+EExfdjXdxX7wsWQRBdFQQNBAMPUUEDhUsEA40VDIwUuVCRMxNBDUSDSww0UEFBkAMTDQwPVJY7UNTkEhHv/GoeWlc7szOLNyDoDz8zW391VfV0dfcODf3HX4ZGo7G60+kssfY4iK+MsfZM4Jw7CK8MWmC1Wr3GuKNW6wFO++AMnFf8Aj8G77MSrNVqrYoYuw0+azabG60mKJfLy2q12km4xmqlUmk9Yx/V6/VdVosEzjfhd4rZY+zbpViSPM7n8ytCuyTH9wH2E9of+zpsx9FuM+4rfA83aZ8Q+B2wcSPRbrdXEuQFnGJGBa3JYOzP4RxJ94d2CY7tjfUPCjxSqVR24H+/X4HSh2gv7SR7gNNm+BlO8HNYayRZi/2VW/h1c7zfwjaufS1IfKdfgQK0sai8C8BsDzu/385aDdtu+A1OhjuvWCxu4Pdbl9DkKQscER96smy1X8Bh3EX0X7AET+EnWbLQjl8HfpCn9rdIU6DEQO8Sf6fVPKgek690F94QBsGnZSnt7LAdQpvh2dB2izQFiiY+EtNqHtzv/ntCw7tggEcSLLX+gqDAvokFgxQIR63mQfXfBavFIaMCe/rfg/P7b66qjpAkZFFg5BKr8+8d51fJ6nGQzcSYaVpiq9U00hQofSyx4IjVZHm3OP+0fxjXb1Fwft/KBur71YMCu3aTacjuxWdKYmrj3mBm84py/55SY2MR7nwKOG01uZedvyqzKvYP2MX/jPXHPiqxEq+7QUGyiy7pBkjGMDHuSSwr/DHo2RbBX0ubWC0tghiT8rTaooDg5+BVXnNWS4EcX+4SfXxe3q24KJA/nhR4HR6zWhKCfTCR+T/rQqGwnESXk649DTnSGDOWeXH/LH4CPb/QdrG5MIcAAAAASUVORK5CYII=>