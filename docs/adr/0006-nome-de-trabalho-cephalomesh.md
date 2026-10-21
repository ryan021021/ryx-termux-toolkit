# ADR-0006 — Nome de trabalho: cephalomesh

Estado: ACEITA (21/10/2026; o mantenedor delegou a escolha). Complementa a ADR-0005, sem substituí-la no código.

## Contexto

"KRAKEN MESH" tem os identificadores exatos livres, mas conflito material provável (FASE0 §3): `uber/kraken`
no mesmo domínio técnico, marca forte de cripto e uma ferramenta de C2 com o mesmo nome. Das cinco
alternativas, todas livres no PyPI, no npm e em nomes de repositório do GitHub em 20/10:

- **cephalomesh** conta a arquitetura: um cérebro central e gânglios em cada braço que decidem sozinhos é
  exatamente o par standalone + mesh com coordenador como papel;
- é o único que não carrega associação com outro produto conhecido;
- é pronunciável em português e em inglês.

## Decisão

- Nome de trabalho do produto: **cephalomesh** (docs, specs e material de marca futuro).
- Pacote, CLI e repositório continuam `ryx` / `ryx-termux-toolkit`. A troca no código só vem depois de
  conferir marcas (INPI, EUIPO, USPTO) e numa ADR própria que liste os arquivos.
- KRAKEN MESH e EDGEWARD ficam como nomes das diretivas de origem, não do produto.

## Consequências

- Nenhum arquivo de código muda agora.
- A checagem de marca entra no backlog antes de qualquer publicação.
