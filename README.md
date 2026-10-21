<p align="center"><img src="assets/banner.svg" alt="ryx-termux-toolkit" width="640"></p>

# ryx-termux-toolkit

Toolkit modular de linha de comando para o **Termux** (Android): diagnóstico do ambiente, bloco gerenciado no
`.bashrc`/`.zshrc`, pacotes recomendados, estado do servidor, rotinas de backup e detecção de CLIs de IA.

> **Status: experimental (v0.1.0).** Os testes automatizados passam, mas ele **ainda não foi validado num
> aparelho real** e a CI **nunca rodou** (o repositório nasceu local e privado). Leia
> [Limitações](#limitações) antes de confiar nele.

## Por que existe

- **Nada grava sem você pedir.** Todo comando que escreve é simulação por padrão; só `--apply` grava, e ação
  sensível exige também `--yes`.
- **Só biblioteca padrão do Python (3.11+).** Zero dependências em tempo de execução, nada de rede ao importar.
- **Reversível.** O bloco do shell é idempotente, tem backup antes de gravar e a remoção devolve o arquivo
  byte a byte. Backups têm manifesto e SHA-256, e a restauração recusa caminho fora do destino.
- **Honesto.** Cada módulo declara sua estabilidade; hoje todos são `experimental`.

## Instalação rápida

Num clone do repositório (veja [docs/INSTALLATION.md](docs/INSTALLATION.md) para todas as opções):

```sh
sh scripts/check-environment.sh      # só confere o ambiente
sh install.sh --dry-run              # mostra o que faria
sh install.sh                        # instala (pip --user) e roda o doctor
```

Sem instalar nada, direto da árvore do código: `PYTHONPATH=src python -m ryx doctor`.

## Uso

```sh
ryx doctor                      # diagnóstico (ok / aviso / falha), --json para scripts
ryx info                        # versão, plataforma e pastas
ryx modules                     # módulos ligados e sua estabilidade

ryx shell install               # simula; com --apply grava o bloco no ~/.bashrc
ryx shell uninstall --apply     # remove só o bloco do ryx
ryx packages check              # o que falta dos pacotes recomendados
ryx server status               # sshd, serviços runit e wake-lock (no Termux)
ryx backup create --apply       # backup da config e do estado
ryx backup verify <arquivo>     # confere manifesto e SHA-256
ryx automation list             # rotinas fechadas: doctor, backup-config, prune-backups
ryx ai check                    # quais CLIs de IA existem e se há chave (nunca mostra a chave)
```

Referência completa: [docs/COMMANDS.md](docs/COMMANDS.md).

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `src/ryx/` | pacote: `cli`, `config`, `paths`, `platform`, `permissions`, `backup`, `state`, `logger`, `registry` e `modules/` |
| `templates/` | trechos de shell (bash/zsh) e temas |
| `config/` | `default.toml` (valores) e `modules.toml` (liga/desliga módulos) |
| `scripts/` | verificações e geração de notas de versão |
| `tests/` | `unit`, `integration`, `installer` e `security` |
| `docs/` | arquitetura, comandos, módulos, segurança e solução de problemas |

## Limitações

- Nunca rodou num aparelho real nem na CI; o desenvolvimento e os testes foram feitos no Windows e no Git Bash.
- Sem sistema de plugins, sem painel web e sem agendador próprio (o `ryx automation crontab` só *sugere* linhas).
- `packages install` só funciona no Termux e depende do `pkg`.
- Detalhes por módulo em [docs/MODULES.md](docs/MODULES.md).

## Desenvolvimento

```sh
python -m unittest discover -s tests -t .     # toda a suíte (~40 s)
python -m ruff check . && python -m ruff format --check .
```

Regras de engenharia e definição de pronto: [docs/ENGINEERING_CHARTER.md](docs/ENGINEERING_CHARTER.md).
Veja também [CONTRIBUTING.md](CONTRIBUTING.md) e [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
Segurança: [SECURITY.md](SECURITY.md). Licença: [MIT](LICENSE).
