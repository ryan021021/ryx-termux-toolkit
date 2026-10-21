# Desenvolvimento

Veja primeiro o [CONTRIBUTING.md](../CONTRIBUTING.md). Aqui ficam os detalhes técnicos do dia a dia.

## Ambiente

Python 3.11+, sem dependências em tempo de execução. Para lint, `pip install ruff` (opcional).

```sh
git clone <seu-clone> ryx-termux-toolkit && cd ryx-termux-toolkit
PYTHONPATH=src python -m ryx doctor      # roda direto da árvore
```

## Testes

```sh
python -m unittest discover -s tests -t .          # tudo
python -m unittest tests.unit.test_backup          # um arquivo
python -m unittest discover -s tests/installer -t . # instaladores (exigem sh)
```

| Pasta | O que cobre |
|---|---|
| `tests/unit` | funções e módulos isolados, com dependências injetadas |
| `tests/integration` | a CLI de ponta a ponta, em `RYX_HOME` temporário (`CliTestCase.ryx(...)`) |
| `tests/installer` | `install.sh`, `uninstall.sh`, `bootstrap.sh`, `scripts/` com `sh` de verdade |
| `tests/security` | backups hostis, varredura estática, injeção pela CLI |

Testes que precisam de POSIX ou de `bash` pulam sozinhos no Windows (5 hoje). Defina
`PYTHONDONTWRITEBYTECODE=1` e `PYTHONIOENCODING=utf-8` para uma saída limpa.

## Regras do projeto

- Só biblioteca padrão. O teste de segurança falha se aparecer outro `import`.
- Sem caminho pessoal, nome de usuário ou segredo em nenhum arquivo de texto (o mesmo teste varre tudo).
- Todo comando que grava passa por `permissions.decide`.
- Código novo ou bug: escreva o teste que falha primeiro.
- Comentários e mensagens para o usuário em português do Brasil.

## Lint

```sh
python -m ruff check .
python -m ruff format --check .
```

A configuração está em `pyproject.toml` (`E,F,W,I,B,UP,S`). Ainda não foi rodada nesta base.

## Versão e notas de versão

1. Atualize `version` em `pyproject.toml` e `src/ryx/__init__.py`.
2. Escreva a seção `## [X.Y.Z] - AAAA-MM-DD` no `CHANGELOG.md`.
3. `python scripts/generate-release-notes.py X.Y.Z` imprime o texto da versão.
