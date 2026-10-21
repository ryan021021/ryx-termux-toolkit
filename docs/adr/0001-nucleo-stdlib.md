# ADR-0001 — Núcleo em Python só com a biblioteca padrão

Estado: ACEITA (20/10/2026; registra o que o código já faz).

## Contexto

As diretivas pedem núcleo leve, sem root, sem Docker, sem Node e sem dependência obrigatória de IA. O Termux
empacota o Python 3, mas ele **não vem instalado**: o A15 medido na Fase 0 não tinha `python` (achado F2).

## Decisão

- Núcleo em Python ≥ 3.11 usando só a biblioteca padrão; nada de rede ao importar.
- Integrações opcionais (IA, painel, mesh) declaram as próprias dependências e nunca entram no núcleo.
- O Python é o único pré-requisito. O instalador detecta a falta e **pede consentimento** antes de rodar
  `pkg install python`; sem consentimento, para com mensagem clara.

## Consequências

- Sem `cryptography`, sem X.509 gerado em Python: afeta o mesh (ADR-0004).
- O pacote `python` do Termux tem centenas de MB; o instalador mostra o tamanho antes de pedir o OK.
- A suíte roda em qualquer máquina com Python 3.11+, mas só a execução no aparelho prova compatibilidade.
