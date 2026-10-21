# ADR-0005 — Nome provisório, pacote continua `ryx`

Estado: ACEITA (20/10/2026).

## Contexto

Chegaram dois nomes de produto (EDGEWARD e KRAKEN MESH). Ambas as diretivas mandam validar nome e marca antes
de publicar e proíbem renomear em silêncio. A checagem de 20/10 ([FASE0](../specs/FASE0.md#3-validação-do-nome-kraken-mesh))
achou os identificadores exatos livres, mas um conflito material provável com "Kraken".

## Decisão

- Pacote, CLI e repositório continuam `ryx` / `ryx-termux-toolkit` até o mantenedor escolher o nome.
- A troca, quando vier, é uma ADR nova que lista os arquivos alterados e as checagens de marca feitas.
- Nenhum material de marca (logo, banner) com o nome novo antes dessa ADR.

## Consequências

- Docs e specs usam o nome do produto como "proposta"; o código não muda.
