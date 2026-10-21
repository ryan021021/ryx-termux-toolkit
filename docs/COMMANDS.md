# Comandos

Convenções: comando que grava é **simulação** sem `--apply`; ação sensível exige `--apply --yes`.
Códigos de saída: `0` ok · `1` falha ou erro do usuário (`erro: ...` no stderr) · `2` uso incorreto · `130` Ctrl-C.

| Flag global | Efeito |
|---|---|
| `--version` | imprime `ryx X.Y.Z` |
| `-h`, `--help` | ajuda (também em cada subcomando) |

## Núcleo

| Comando | Risco | O que faz |
|---|---|---|
| `ryx modules` | leitura | lista módulos, estabilidade e se estão ligados |
| `ryx backup create [--path P]... [--apply]` | reversível | backup de `config/`, `state.json` e caminhos extras |
| `ryx backup list` | leitura | lista os backups da pasta de backups |
| `ryx backup verify ARQUIVO` | leitura | confere manifesto e SHA-256; sai com 1 se houver problema |
| `ryx backup restore ARQUIVO --to PASTA [--apply]` | reversível | restaura **só dentro** de `PASTA`; recusa conflito |
| `ryx backup restore ... --overwrite --apply --yes` | sensível | sobrescreve o que já existe |
| `ryx backup prune --apply --yes` | sensível | mantém os `backup.keep` mais novos |

## `diagnostics`

| Comando | O que faz |
|---|---|
| `ryx doctor [--json]` | Python, ambiente, comandos (`git`, `ssh`, `curl`), disco, memória, config e estado. Sai com 1 se alguma checagem for FALHA |
| `ryx info` | versão, plataforma e as pastas em uso |

Limites: disco livre < 100 MB = FALHA, < 500 MB = aviso; memória disponível < 200 MB = aviso.

## `shell`

`ryx shell status|install|uninstall [--shell bash|zsh] [--theme NOME] [--apply]`

Grava/remove o bloco entre `# >>> ryx >>>` e `# <<< ryx <<<` em `~/.bashrc` (padrão `shell.rc_files`).
Faz backup antes de gravar, não mexe fora do bloco e repetir o comando não muda nada. Temas: `default`, `minimal`.
Marcador quebrado no arquivo é erro (nada é gravado).

## `packages`

`ryx packages check [--add PACOTE]...` · `ryx packages install [--add PACOTE]... [--apply]`

Confere com `dpkg-query`; `install` roda `pkg install -y <faltantes>` **só no Termux** e só com `--apply`.
Nomes de pacote seguem `^[a-z0-9][a-z0-9+.-]{0,63}$`.

## `server`

`ryx server status` — sshd na porta `server.ssh_port`, serviços runit de `server.services` e `termux-wake-lock`.
Só leitura. Fora do Termux só avisa.

## `automation`

| Comando | Risco | O que faz |
|---|---|---|
| `ryx automation list` | leitura | lista as rotinas e o risco de cada uma |
| `ryx automation run doctor` | leitura | roda o diagnóstico |
| `ryx automation run backup-config [--apply]` | reversível | backup de config e estado |
| `ryx automation run prune-backups [--apply --yes]` | sensível | apaga backups além de `backup.keep` |
| `ryx automation crontab` | leitura | imprime linhas de cron **sugeridas** (não instala) |

## `ai`

`ryx ai check` — para cada provedor em `ai.providers` (`claude`, `gemini`, `codex`): instalado?, versão e se a
variável de chave existe no ambiente (`sim`/`não`). **Nunca imprime o valor da chave.**

## Configuração

Arquivo `~/.config/ryx/config.toml` (ou `$RYX_HOME/config/config.toml`). Chaves aceitas:

```toml
[core]      log_level = "info"                       # debug|info|warning|error
[backup]    keep = 10
[shell]     theme = "default"                        # e rc_files = ["~/.bashrc"]
[packages]  recommended = ["git", "openssh", "curl", "python", "jq", "nano"]
[server]    ssh_port = 8022                          # e services = ["sshd"]
[ai]        providers = ["claude", "gemini", "codex"]
```

`modules.toml` na mesma pasta liga/desliga módulos: `[modules]` com `ai = false`, por exemplo.
Variáveis: `RYX_HOME`, `RYX_RESOURCES`, `RYX_LOG_FILE=1` (grava `ryx.log` em `state/`), `RYX_LOG_FORMAT=json` (log estruturado em JSON com hora, nível, módulo e mensagem mascarada).

