## O que muda

## Por quê

## Como foi testado

- [ ] `python -m unittest discover -s tests -t .` passa
- [ ] teste novo que falhava antes da mudança
- [ ] `python -m ruff check .` sem achados
- [ ] nada grava sem `--apply`; ação sensível exige `--yes`
- [ ] sem dependência fora da biblioteca padrão
- [ ] `CHANGELOG.md` atualizado (seção *Não lançado*)
