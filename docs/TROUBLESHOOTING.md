# Solução de problemas

Comece sempre por `ryx doctor` (ou `ryx doctor --json`) e `ryx info`.

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `ryx: command not found` | `~/.local/bin` fora do `PATH` | acrescente ao `PATH` ou use `python -m ryx` |
| `erro: ... chave desconhecida` | `config.toml` com chave que não existe | corrija a chave; o `ryx doctor` ainda roda e mostra o erro |
| `erro: módulo desconhecido` | nome errado em `modules.toml` | use os nomes de `ryx modules` |
| Template ou tema não encontrado | recursos não foram copiados | rode `sh install.sh --no-pip` ou defina `RYX_RESOURCES` |
| `shell install` diz que o marcador está quebrado | só um dos marcadores `# >>> ryx >>>` / `# <<< ryx <<<` existe | corrija à mão; o `ryx` não grava nada nesse estado |
| `packages install` não faz nada | fora do Termux, ou sem `--apply` | confira `ryx info`; sem `--apply` é só simulação |
| `backup restore` recusa | conflito com arquivo existente, ou caminho inseguro no backup | restaure em pasta vazia; `--overwrite --apply --yes` só se tiver certeza |
| `backup verify` falha | arquivo truncado, adulterado ou sem o `.sha256` ao lado | recrie o backup; não restaure um arquivo que não passa |
| Disco < 100 MB no `doctor` | pouco espaço | libere espaço; `ryx backup prune --apply --yes` remove backups antigos |
| `ryx server status` só avisa | não está no Termux | esperado; o módulo só inspeciona o Termux |
| Saída 1 num script | alguma checagem do `doctor` é FALHA | leia a linha `[FALHA]`; use `--json` para tratar |

## Isolar para testar

```sh
export RYX_HOME="$(mktemp -d)"     # config, dados, estado e backups ficam aqui
RYX_LOG_FILE=1 ryx doctor          # grava o log em $RYX_HOME/state/ryx.log
```

Nada fora de `RYX_HOME` é tocado, exceto o `.bashrc` quando você usa `shell install --apply`.

## Pedindo ajuda

Abra uma issue com `ryx --version`, a saída de `ryx info`, o comando executado e a mensagem de erro.
**Não cole chaves, tokens ou o conteúdo do seu `.bashrc`.** Vulnerabilidade: veja [SECURITY.md](../SECURITY.md).
