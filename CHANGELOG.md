# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versões: [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Corrigido
- `uninstall.sh --purge` apaga só `templates/` e `config/` da pasta de dados; `backups/` fica.
- `bootstrap.sh` exige `RYX_COMMIT` (ou `RYX_INSECURE=1`); limpa a pasta temporária e sai com 130 em Ctrl-C.
- Backup: ordem por (carimbo, contador), nome reservado com `O_EXCL`, hash e conteúdo da mesma leitura,
  verificação final, fontes repetidas deduplicadas, `--path` inexistente é erro.
- Arquivos ilegíveis (UTF-8 inválido, JSON/TOML aninhado demais) viram erro claro em vez de traceback.
- `safe_relative` recusa `.` e `:`; a restauração recusa destinos repetidos ou aninhados antes de gravar.
- `packages`: "não achou" e "não consegui consultar" são coisas diferentes (`desconhecido`).
- `install.sh --strict` sai com 1 se o doctor reportar FALHA; scripts rodam o python com `-P`.
- Máscara de segredos cobre JSON, `--token x`, `GITHUB_TOKEN=`, URL com senha e aspas com espaço;
  log em `0600`, pasta de backups `0700`.
- `shell`: valida o estado antes de gravar o rc, recusa `rc_files` fora do HOME e segue link simbólico.

## [0.1.0] - 2026-10-20

### Adicionado
- CLI `ryx` com os módulos `shell`, `diagnostics`, `packages`, `server`, `automation` e `ai`.
- Escritas são simulação (dry-run) por padrão; só `--apply` grava; operação sensível exige também `--yes`.
- Backup em `.tar.gz` com manifesto e SHA-256, verificação e restauração que recusa caminho fora do destino.
- Bloco gerenciado no `~/.bashrc`/`~/.zshrc` (instalação idempotente, remoção só do bloco, backup antes de gravar).
- `install.sh`, `uninstall.sh`, `bootstrap.sh` e scripts de verificação.
- Testes unitários, de integração, de instalador e de segurança; workflows de CI (testes, lint, segurança).

### Limitações conhecidas
- Ainda não validado em aparelho real; a CI nunca rodou (o repositório é local).
- Sem plugins, sem painel web e sem agendador próprio (veja `docs/MODULES.md`).
