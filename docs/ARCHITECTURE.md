# Arquitetura

O `ryx` é um pacote Python só com biblioteca padrão. Um núcleo pequeno (config, caminhos, permissões, backup,
estado, log) e seis módulos que plugam subcomandos na CLI.

```
cli.main ─► resolve_paths ─► _load(config + modules.toml) ─► build_registry ─► argparse ─► módulo.run(args, ctx)
                                                                                       │
                          Context(paths, config, logger, platform, out, config_error) ◄─┘
```

## Núcleo (`src/ryx/`)

| Arquivo | Responsabilidade |
|---|---|
| `cli.py` | monta o `argparse`, carrega config, trata erros e define os códigos de saída |
| `paths.py` | `Paths` (config/dados/estado/backups) a partir do ambiente; `find_resource` |
| `config.py` | camadas `BUILTIN_DEFAULTS` → `config/default.toml` → `config.toml` do usuário; chave desconhecida é erro |
| `permissions.py` | `Risk` (READ/REVERSIBLE/SENSITIVE), `decide()`, `safe_relative`, `inside` |
| `backup.py` | `.tar.gz` com `manifest.json` + `.sha256`; verificação e restauração segura |
| `state.py` | `state.json` versionado, escrita atômica com modo `0600` |
| `logger.py` | log com máscara de segredos (`redact`) |
| `platform.py` | detecta Termux, Android e shell; `run_text` executa comando com *timeout* |
| `registry.py` | `ModuleSpec`, `Registry`, `Context` e a lista `MODULE_NAMES` |

## Módulos (`src/ryx/modules/`)

Cada módulo expõe `SPEC` (nome, resumo, estabilidade), `add_parser(subparsers)` e `run(args, ctx) -> int`.
O módulo recebe o `Context`; ele **não** lê variável de ambiente nem toca o `HOME` por conta própria, o que
deixa tudo testável com `tests/helpers.make_ctx`. Funções puras e dependências injetadas (`which`, `runner`,
`connect`, `disk_usage`) permitem testar sem Termux.

## Decisões

1. **Simulação por padrão.** `decide(risk, apply, yes)` é o único ponto que autoriza gravar; ver
   [SECURITY.md](SECURITY.md).
2. **Config fechada.** Chave desconhecida falha cedo; o `doctor` ainda roda e mostra o erro.
3. **Rotinas fechadas.** `automation` executa só funções embutidas; config não vira comando.
4. **Recursos fora do pacote.** `templates/` e `config/` são copiados para a pasta de dados pelo `install.sh`
   (ou achados via `RYX_RESOURCES`, ou na árvore do código). O pacote pip não os carrega.
5. **Escrita atômica.** Estado, `.bashrc` e arquivos restaurados usam arquivo temporário + `os.replace`.

## Pastas em disco

| O quê | Padrão | Com `RYX_HOME=/x` |
|---|---|---|
| config do usuário | `~/.config/ryx/` | `/x/config/` |
| recursos copiados | `~/.local/share/ryx/` | `/x/data/` |
| estado e log | `~/.local/state/ryx/` | `/x/state/` |
| backups | `~/.local/share/ryx/backups/` | `/x/backups/` |

`XDG_CONFIG_HOME`, `XDG_DATA_HOME` e `XDG_STATE_HOME` são respeitados quando `RYX_HOME` não está definido.
Ordem de busca de recursos: `RYX_RESOURCES`, depois a pasta de dados, depois a árvore do código.
