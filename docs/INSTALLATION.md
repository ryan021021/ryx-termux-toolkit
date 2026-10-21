# Instalação

Requisitos: Python **3.11+**. No Termux: `pkg install python git`. Sem root.

> O repositório é privado por enquanto e não há pacote no PyPI. Instale sempre a partir de um clone.

## 1. Conferir o ambiente

```sh
sh scripts/check-environment.sh
```

Só lê. Sai com 1 se faltar Python 3.11+.

## 2. Instalar

```sh
sh install.sh --dry-run     # mostra tudo o que faria
sh install.sh               # instala
```

O que o `install.sh` faz, nesta ordem:

1. confere o Python;
2. `python -m pip install --user --upgrade .` (no Termux, sem `--user`);
3. copia `templates/` e `config/` para a pasta de dados (`~/.local/share/ryx`);
4. roda `python -m ryx doctor` e mostra o resultado; se o doctor reportar FALHA, a última linha diz
   `doctor reportou FALHA` (e com `--strict` o script sai com 1).

Opções: `--dry-run`, `--no-pip` (só copia recursos; para desenvolvimento com `PYTHONPATH=src`),
`--skip-doctor`, `--strict` (sai com 1 se o doctor reportar FALHA). Variáveis: `PYTHON`, `RYX_HOME` (isola tudo numa pasta), `RYX_PIP_ARGS` (argumentos extras do pip).
Pode rodar de novo: o resultado é o mesmo.

Se o `ryx` não for encontrado depois, acrescente `~/.local/bin` ao `PATH` ou use `python -m ryx`.

## 3. Bloco do shell (opcional)

```sh
ryx shell install              # simula
ryx shell install --apply      # grava o bloco no ~/.bashrc (faz backup antes)
```

## 4. A partir de um repositório remoto

```sh
RYX_REPO_URL=<url-do-seu-repo> RYX_COMMIT=<sha completo> RYX_REF=main sh bootstrap.sh --dry-run
```

O `bootstrap.sh` clona numa pasta temporária, **exige e confere o commit** (`RYX_COMMIT`) e roda o
`install.sh` repassando as opções. Sem `RYX_COMMIT` ele recusa; só `RYX_INSECURE=1` (valor exato) instala sem
conferir, por sua conta e risco. A pasta temporária some ao terminar, falhar ou receber Ctrl-C. Não existe URL padrão de propósito.

## 5. Conferir depois

```sh
sh scripts/verify-install.sh
```

## Desinstalar

```sh
sh uninstall.sh --dry-run
sh uninstall.sh                    # remove o bloco do shell e o pacote; mantém config, estado e backups
sh uninstall.sh --purge --yes      # também apaga templates/ e config/ copiados (só eles; backups/ fica)
```

Config, estado e backups **nunca** são apagados pelo desinstalador.
