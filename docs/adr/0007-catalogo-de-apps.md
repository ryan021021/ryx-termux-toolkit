# ADR-0007 — Catálogo de apps: manifesto por app, recusa por padrão

Estado: PROPOSTA (21/10/2026). Vira ACEITA quando o validador (`src/ryx/apps.py`, T125) existir e provar cada regra abaixo com teste.

## Contexto

O objetivo é "baixar e testar apps fácil" num Android sem root (`docs/PLANO_SERVIDOR_2026.md` do repositório
`celular`; OMNISERVER §8 e §11). O Android dá um UID só ao Termux: não há contêiner nem usuário isolado, então um
app instalado roda com as mesmas permissões do servidor. Por isso o catálogo precisa **recusar o que for duvidoso
antes de instalar**, e dizer ao usuário o que não consegue garantir, em vez de fingir isolamento.

## Decisão

Cada app tem um manifesto `app.json` (só `json` da stdlib; nada de YAML). Campos, todos obrigatórios, sem
campo extra (campo desconhecido é erro):

| Campo | Tipo | Regra |
|---|---|---|
| `id` | texto | `^[a-z][a-z0-9-]{2,31}$` |
| `name`, `version` | texto | não vazio |
| `kind` | texto | `termux-pkg` ou `download` |
| `package` | texto | só em `termux-pkg`: nome de pacote válido (`^[a-z0-9][a-z0-9+.-]*$`) |
| `source` | objeto | só em `download`: `url` (https) e `sha256` (64 hex minúsculos) |
| `bind` | texto | exatamente `127.0.0.1` |
| `port` | inteiro | 1024 a 65535 |
| `data_dir` | texto | relativo, sem `..`, e dentro de `ryx-apps/<id>/` |
| `service` | objeto | `name` (igual ao `id`) e `run` (lista de textos, nunca uma linha de shell) |
| `route` | objeto | `path_prefix` começando em `/` |
| `health` | objeto | `path` (começa em `/`), `expect_status` (100 a 599), `timeout_s` (1 a 60) |
| `uninstall` | objeto | `remove_dirs`: lista de caminhos relativos, todos dentro de `data_dir` |
| `personal_data` | booleano | `true` é recusado no modo pessoal |

Regras de recusa (cada uma ganha um teste que falha se a regra for removida):

1. `id` inválido, campo ausente ou campo desconhecido.
2. `source.url` que não seja `https`, ou `sha256` ausente ou mal formado (em `download`).
3. `bind` diferente de `127.0.0.1`, ou `port` fora da faixa.
4. `data_dir` ou `uninstall.remove_dirs` absoluto, com `..` ou fora da pasta do app.
5. `service.run` que não seja lista de textos, ou com texto vazio.
6. `health` ausente ou com valores fora da faixa.
7. `personal_data: true`.

Instalar (tarefa futura, não faz parte deste ADR): mostrar o plano e só aplicar com `--apply` (simulação por padrão,
como o resto do `ryx`) → baixar conferindo o `sha256` → criar o serviço → criar a rota → rodar o teste de saúde.
Se o teste falhar, desfazer **só o que o próprio ryx criou**.

## O que o catálogo não garante

- Isolamento entre apps: um app instalado enxerga o que o Termux enxerga.
- Que o pacote exista no Termux: o primeiro app (gerenciador de arquivos web, ex.: filebrowser) fica só no papel
  até alguém conferir a disponibilidade (NOT VERIFIED).
- Nada é baixado nem escrito no aparelho por este ADR; o validador só lê um arquivo JSON.

## Consequências

- Manifesto inválido nunca chega a rede nem a disco: o validador devolve a lista de erros e a instalação nem começa.
- O formato é o contrato entre o validador, o instalador futuro e o painel novo (T120).
