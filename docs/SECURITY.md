# Modelo de segurança

Complementa a [política](../SECURITY.md) (como reportar). Aqui está o que o `ryx` promete e como cada
promessa é testada. **Nada disto foi auditado por terceiros.**

## Princípios

1. **Simulação por padrão.** Ação com efeito só roda com `--apply`; ação sensível também exige `--yes`.
   `permissions.decide(risk, apply, yes)` é o único portão.
2. **Sem execução de texto.** O código não usa `eval`, `exec`, `os.system` nem `shell=True`. Todo comando
   externo é uma lista de argumentos com *timeout*.
3. **Entrada é dado.** Nome de pacote, serviço, tema e entradas do manifesto de backup são validados antes do uso.
4. **Segredo não sai.** Chaves de API são lidas só para saber se existem; o logger mascara
   `token`, `secret`, `password`, `api key` e `Authorization` (inclusive `Bearer`/`Basic`).
5. **Escrita contida.** A restauração só escreve dentro do destino: rejeita caminho absoluto, `..`,
   *symlink* para fora, modo inválido e entrada duplicada ou conflitante.
6. **Arquivos privados.** Estado, backups, `.sha256` e log são gravados com modo `0600` (pasta de backups `0700`, só em POSIX), de forma atômica.

## Ameaças consideradas

| Ameaça | Defesa | Teste |
|---|---|---|
| Backup forjado escreve fora do destino | `safe_relative`, `inside`, verificação de SHA-256 antes de extrair | `tests/security/test_hostile_backup.py` |
| Manifesto malformado ou arquivo truncado | `_read_manifest`, `_entry_mode`, `verify_backup` devolvem `BackupError` | `tests/security/test_hostile_backup.py` |
| Injeção por argumento ou config | listas de argumentos, regex de nome, config fechada | `tests/security/test_cli_injection.py` |
| Vazamento de chave | máscara no logger, `ai check` mostra só sim/não | `tests/security/test_cli_injection.py`, `tests/unit/test_logger.py` |
| Segredo ou caminho pessoal no repositório | varredura de todos os arquivos de texto | `tests/security/test_static_scan.py` |
| `uninstall --purge` apagar a pasta errada ou os backups | recusa vazio, `/`, `$HOME`; compara caminhos reais; apaga só `templates/` e `config/` da pasta de dados | `tests/installer/test_scripts.py` |
| `bootstrap.sh` instalar código trocado | exige URL explícita e `RYX_COMMIT` (ou `RYX_INSECURE=1` explícito) e confere o commit | `tests/installer/test_scripts.py` |
| `ryx/` plantado na pasta atual sequestrar `python -m ryx` | os scripts rodam o python com `-P` | `tests/installer/test_scripts.py` |
| Backup ordenado errado apagar o mais novo / nome sobrescrito | ordem por (carimbo, contador); nome reservado com `O_EXCL`; verificação final do arquivo | `tests/unit/test_backup.py` |

## Fora do modelo

- Atacante com root no aparelho ou acesso ao seu usuário já autenticado.
- Qualquer coisa que o próprio Termux, o `pkg` ou o `pip` façam.
- Confiar em `RYX_REPO_URL`: quem aponta para um repositório confia nele. `RYX_COMMIT` é obrigatório.

## Lacunas honestas

- Ainda não rodou num aparelho real nem na CI.
- `ruff` e `shellcheck` não foram executados na máquina de desenvolvimento.
- Os testes de segurança são de caixa-branca escritos pelo próprio autor; revisão externa seria bem-vinda.
