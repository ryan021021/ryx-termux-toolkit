# ADR-0003 — Capacidades com estado e frescor

Estado: PROPOSTA. É a primeira fatia da Fase 1.

## Contexto

O `doctor` atual devolve ok/aviso/falha. As diretivas pedem capacidades com cinco estados e frescor, e a
Fase 0 mostrou leituras que o Android nega (`/proc/loadavg`, achado F4) e ferramentas ausentes (`python`,
`openssl`, `zsh`).

## Decisão

Cada capacidade é um registro imutável:

```text
id          ex.: "runtime.python", "battery.read", "service.runit"
state       SUPPORTED | UNSUPPORTED | UNKNOWN | TEMPORARILY_UNAVAILABLE | NEEDS_CONFIGURATION
evidence    o que foi lido (comando ou arquivo) e o resultado, sem segredo
measured_at hora da medida (UTC)
ttl_s       por quanto tempo a medida vale; depois disso o estado exibido é STALE
```

- Leitura negada vira `UNSUPPORTED` com a evidência, nunca zero.
- Pacote instalado sem teste de uso vira `UNKNOWN`, não `SUPPORTED`.
- `ryx doctor --json` passa a listar capacidades; a saída antiga continua até a migração terminar.

## Consequências

- O agendador futuro decide só por capacidades frescas.
- Fixtures por perfil de aparelho (a A15 medida na Fase 0 é a primeira) e testes de "leitura negada".
