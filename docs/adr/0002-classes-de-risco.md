# ADR-0002 — Classes de risco L0–L3 sobre o `decide()` atual

Estado: PROPOSTA.

## Contexto

Hoje `permissions.decide(risk, apply, yes)` tem três níveis (`READ`, `REVERSIBLE`, `SENSITIVE`) presos a
flags da CLI. As diretivas pedem quatro classes, aprovação presa à operação exata e "nega por padrão".

## Decisão

| Hoje | Nova classe | Regra |
|---|---|---|
| `READ` | L0 | executa dentro do escopo |
| — | L1 | **não existe** até haver política escrita para uma operação específica (nega) |
| `REVERSIBLE` | L2 | plano + backup + `--apply` |
| `SENSITIVE` | L3 | plano + `--apply --yes`; nunca automático, nunca aprovado por agente |

- A aprovação passa a carregar o **hash do plano** (operação, argumentos, alvo, versão). Se o plano executado
  tiver outro hash, nega.
- Operação sem classe declarada é L3 (nega por padrão).
- Migração em fatia própria, com testes que provem que nenhum comando atual muda de comportamento.

## Consequências

- `decide()` ganha um parâmetro de plano; os chamadores atuais continuam válidos durante a migração.
- Agentes (fase 6) só chegam a L0/L1 por política; L2/L3 sempre passam por humano.
