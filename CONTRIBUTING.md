# Como contribuir

Obrigado por querer ajudar. O projeto é pequeno de propósito; estas regras mantêm assim.

## Antes de começar

1. Abra uma *issue* descrevendo o problema ou a ideia (use os modelos em `.github/ISSUE_TEMPLATE/`).
2. Mudança que mexe em segurança, backup ou no que o `--apply` grava precisa ser discutida antes.
3. Vulnerabilidade **não** vai em issue pública: veja [SECURITY.md](SECURITY.md).

## Ambiente

```sh
python -m venv .venv && . .venv/bin/activate     # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -t .
```

Python 3.11 ou mais novo. Em tempo de execução **só biblioteca padrão**: dependência nova em `dependencies`
precisa de justificativa forte.

## Regras do código

- Escrita no disco ou no sistema passa por `ryx.permissions.decide` (simulação por padrão).
- Nada de `shell=True`, `eval`, `exec`, `os.system`; subprocesso só com lista de argumentos e *timeout*
  (o teste `tests/security/test_static_scan.py` barra isso).
- Entrada externa (argumento, config, manifesto de backup, nome de pacote/serviço/tema) é validada na borda
  e vira `UserError`/`ConfigError`/`BackupError`, nunca traceback.
- Segredo nunca é impresso nem logado; use `ryx.logger.redact`.
- Texto para o usuário em português do Brasil; identificadores e commits em inglês técnico curto também são aceitos.
- Sem caminhos pessoais, e-mails ou chaves no repositório (o mesmo teste confere).

## Testes

- Código novo ou bug: escreva o teste que **falha primeiro**, depois a correção.
- Teste de comportamento, não de implementação. Use `tests/helpers.make_ctx` para um contexto isolado.
- Nenhum teste toca o `HOME` real: use `RYX_HOME` e pastas temporárias.
- `ruff check` e `ruff format --check` precisam passar.

## Commits e pull requests

- Mensagens no formato `tipo: resumo` (`feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`).
- Um assunto por PR; preencha o modelo de PR e diga **como testou** e o que **não** foi testado.
- Atualize `CHANGELOG.md` (seção `[Unreleased]`) quando mudar comportamento visível.

## Conduta

Participar significa aceitar o [Código de Conduta](CODE_OF_CONDUCT.md).
