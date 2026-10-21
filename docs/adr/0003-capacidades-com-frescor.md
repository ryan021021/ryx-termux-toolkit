# ADR-0003 — Capacidades com estado e frescor

Estado: ACEITA (21/10/2026, T104). É a primeira fatia da Fase 1; código em `src/ryx/capabilities.py`.

## Contexto

O `doctor` atual devolve ok/aviso/falha. As diretivas pedem capacidades com cinco estados e frescor, e a
Fase 0 mostrou leituras que o Android nega (`/proc/loadavg`, achado F4) e ferramentas ausentes (`python`,
`openssl`, `zsh`).

## Decisão

Cada capacidade é um registro imutável:

```text
id          ex.: "runtime.python", "command.git", "proc.loadavg", "battery.read"
state       SUPPORTED | UNSUPPORTED | UNKNOWN | TEMPORARILY_UNAVAILABLE | NEEDS_CONFIGURATION
evidence    o que foi lido (comando ou arquivo) e o resultado, sem segredo
measured_at hora da medida (UTC)
ttl_s       por quanto tempo a medida vale; depois disso `stale: true` (o estado medido não é trocado)
```

- Leitura negada vira `UNSUPPORTED` com a evidência, nunca zero.
- Pacote instalado sem teste de uso vira `UNKNOWN`, não `SUPPORTED`.
- `ryx doctor --json` passa a listar capacidades; a saída antiga continua até a migração terminar.

## Consequências

- O agendador futuro decide só por capacidades frescas.
- Fixtures por perfil de aparelho (a A15 medida na Fase 0 é a primeira) e testes de "leitura negada".

## Como ficou na T104

- `ryx doctor --json` ganhou a lista `capabilities` (`id`, `state`, `evidence`, `measured_at`, `ttl_s`,
  `stale`); a saída em texto e as chaves `status` e `checks` não mudaram.
- Python é lido do próprio interpretador (`runtime.python`), sem abrir processo: no Windows, rodar
  `python3 --version` acionou o instalador do Python e baixou 179 MB para a pasta corrente. Nenhuma sonda
  pode ter efeito colateral; o teste `test_collect_nunca_roda_python_como_comando` guarda isso.
- Prova no A15 (21/10): `proc.loadavg` UNSUPPORTED "leitura negada", `battery.read` SUPPORTED pelo termux-api,
  `runtime.python` 3.14.8. A tabela de TTL é inicial (3600 s para o estático, 60 s para bateria).
