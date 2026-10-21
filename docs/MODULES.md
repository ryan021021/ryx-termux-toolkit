# Módulos

Todos os módulos estão em estágio **experimental** na `0.1.0`. `config/modules.toml` liga e desliga cada um;
`ryx modules` mostra o estado atual.

| Módulo | Para que serve | Grava algo? | Limites conhecidos |
|---|---|---|---|
| `shell` | bloco gerenciado no `.bashrc`/`.zshrc` com atalhos e tema | só com `--apply` (backup antes) | só os temas `default` e `minimal`; arquivos rc vêm de `shell.rc_files` |
| `diagnostics` | `doctor` e `info` | não | checagem de memória e de disco depende do sistema; fora do Termux alguns itens viram aviso |
| `packages` | confere/instala pacotes recomendados | só com `--apply`, só no Termux | usa `dpkg-query` e `pkg`; não resolve conflito de repositório |
| `server` | estado do sshd, serviços runit e wake-lock | não | só leitura; não instala nem reinicia serviço |
| `automation` | rotinas fechadas (`doctor`, `backup-config`, `prune-backups`) e linhas de cron sugeridas | só com `--apply` | não existe agendador próprio; o `crontab` apenas imprime |
| `ai` | detecta CLIs de IA e se há variável de chave | não | nunca mostra a chave; só olha `claude`, `gemini` e `codex` por padrão |

## Como o módulo é escolhido

`registry.MODULE_NAMES` lista os módulos conhecidos. `modules.toml` pode desligar qualquer um (`ai = false`);
nome desconhecido ali é erro de configuração. Módulo desligado não aparece na ajuda nem aceita comando.

## Escrever um módulo novo

1. Crie `src/ryx/modules/<nome>.py` com `SPEC`, `add_parser` e `run(args, ctx)`.
2. Acrescente o nome em `MODULE_NAMES` (`src/ryx/registry.py`) e em `config/modules.toml`.
3. Use `permissions.decide` antes de qualquer escrita e injete dependências externas para testar.
4. Escreva testes em `tests/unit/` e, se tocar o CLI, em `tests/integration/`. O teste estático de
   `tests/security/` já cobre `eval`, `exec`, `os.system` e `shell=True`.
