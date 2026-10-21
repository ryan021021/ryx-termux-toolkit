# Verificação real no aparelho (T97)

Execução de **21/10/2026**, no **A15** (Galaxy A15 5G, Android 16, Termux, sem root, Python 3.14.8, aarch64).
Commit verificado: `5597d76` (copiado com `git archive` para `$TMPDIR/ryx-verif` no aparelho).
A 1ª rodada (CHEFE, com OK do Ryan) achou o teste do bash dependente de caminho fixo, corrigido em `60f2d8c`; esta rodada repete tudo no commit atual e traz as saídas reais.

## Como foi feito

- Nada fora de pastas temporárias: `HOME=$D/home` e `RYX_HOME=$D/ryxhome`, com `D=$TMPDIR/ryx-verif` (`PYTHONPATH=$D/src`).
- Nenhum `pip install` nem `pkg install`: o Python já estava instalado (instalação mínima, sem recomendados, feita na 1ª rodada com OK do Ryan).
- O `.bashrc` mexido é o de teste dentro de `$D/home`; o `.bashrc` real do Termux não foi tocado.
- A pasta `$D` foi removida ao fim.

## Resultado por item

| Item | Resultado | Saída |
|---|---|---|
| Suíte `python -m unittest discover -s tests -t .` | **OK**: 320 testes em 77 s, nenhum pulado | 0 |
| `ryx --version` | **OK**: `ryx 0.1.0` | 0 |
| `ryx doctor` | **OK**: 9 checagens `[ok]` (Python, Termux/Android 16, git, ssh, curl, disco 74 549 MB, memória 1 006 MB, config, estado) | 0 |
| `ryx info` | **OK**: Android, aarch64, Python 3.14.8, `is_termux: True`, pastas dentro de `$D/ryxhome` | 0 |
| `ryx modules` | **OK**: 6 módulos, todos experimentais e ligados | 0 |
| `backup create` (sem `--apply`) | **OK**: só simula e manda acrescentar `--apply` | 0 |
| `backup create --apply` | **OK**: 1 arquivo; avisa `ignorado ... não existe` para `config/` e `state.json` vazios | 0 |
| `backup list` | **OK** | 0 |
| `backup verify` | **OK**: `íntegro` | 0 |
| `backup restore --to ... --apply` | **OK**: 1 arquivo restaurado só dentro da pasta pedida | 0 |
| `shell install --apply` (1ª vez) | **OK**: faz backup do `.bashrc` de teste e grava o bloco | 0 |
| `shell install --apply` (2ª vez) | **OK**: `nada a fazer` (idempotente) | 0 |

Nenhum item ficou FALHA ou BLOCKED nesta rodada.

## Observações

- O aviso falso de `sv` do `ryx server status` (visto na 1ª rodada) está na T106 e não faz parte desta verificação.
- `backup create --apply` sai com 0 mesmo ignorando origens que não existem, avisando em linhas `ignorado:`; esperado em ambiente novo.

## Transcrição (comandos, saídas e códigos de saída reais)

Saídas cortadas em 8 a 30 linhas por comando; `$D` = `/data/data/com.termux/files/usr/tmp/ryx-verif`.

```text
$ python -m unittest discover -s tests -t .
.......... (pontos de progresso omitidos)
.2026-10-21 18:03:34,335 INFO login com password=[REDACTED]
.2026-10-21 18:03:34,338 WARNING não consegui abrir o log em /data/data/com.termux/files/usr/tmp/tmprv26yvm9/arquivo/ryx.log; sigo só na tela
2026-10-21 18:03:34,338 INFO segue só na tela
.......... (pontos de progresso omitidos)
----------------------------------------------------------------------
Ran 320 tests in 77.282s

[exit 0]

$ python -m ryx --version
ryx 0.1.0
[exit 0]

$ python -m ryx doctor
[ok]    python: 3.14
[ok]    ambiente: Termux (Android 16)
[ok]    comando git: /data/data/com.termux/files/usr/bin/git
[ok]    comando ssh: /data/data/com.termux/files/usr/bin/ssh
[ok]    comando curl: /data/data/com.termux/files/usr/bin/curl
[ok]    disco: 74549 MB livres
[ok]    memória: 1006 MB disponíveis
[ok]    config: válida
[ok]    estado: legível
resultado: ok
[exit 0]

$ python -m ryx info
ryx 0.1.0
system: Android
machine: aarch64
python: 3.14.8
is_termux: True
prefix: /data/data/com.termux/files/usr
android_release: 16
shell: bash
config_dir: $D/ryxhome/config
data_dir: $D/ryxhome/data
state_dir: $D/ryxhome/state
backup_dir: $D/ryxhome/backups
[exit 0]

$ python -m ryx modules
shell [experimental, ligado]: Bloco gerenciado no .bashrc/.zshrc (prompt e aliases)
diagnostics [experimental, ligado]: doctor e info: verifica o ambiente sem alterar nada
packages [experimental, ligado]: Confere e instala os pacotes recomendados (pkg)
server [experimental, ligado]: Estado do servidor no Termux: sshd, serviços, wake-lock (só leitura)
automation [experimental, ligado]: Rotinas embutidas (doctor, backup-config, prune-backups)
ai [experimental, ligado]: Detecta CLIs de IA (claude, gemini, codex) e chaves no ambiente
[exit 0]

$ python -m ryx backup create --path $D/home/extra.txt
[simulação] backup de: $D/ryxhome/config, $D/ryxhome/state/state.json, $D/home/extra.txt (simulação: acrescente --apply para gravar)
[exit 0]

$ python -m ryx backup create --path $D/home/extra.txt --apply
backup criado: $D/ryxhome/backups/ryx-20261021-180338.tar.gz (1 arquivo(s))
ignorado: $D/ryxhome/config: não existe
ignorado: $D/ryxhome/state/state.json: não existe
[exit 0]

$ python -m ryx backup list
ryx-20261021-180338.tar.gz
[exit 0]

ARQ=$D/ryxhome/backups/ryx-20261021-180338.tar.gz
$ python -m ryx backup verify $D/ryxhome/backups/ryx-20261021-180338.tar.gz
íntegro
[exit 0]

$ python -m ryx backup restore $D/ryxhome/backups/ryx-20261021-180338.tar.gz --to $D/restaurado --apply
1 arquivo(s) restaurado(s) em $D/restaurado
[exit 0]

$D/restaurado/home/extra.txt
$ python -m ryx shell status
$D/home/.bashrc: não instalado
[exit 0]

$ python -m ryx shell install --apply
backup de $D/home/.bashrc: $D/ryxhome/backups/ryx-20261021-180341.tar.gz
$D/home/.bashrc: bloco gravado
[exit 0]

$ python -m ryx shell install --apply
$D/home/.bashrc: nada a fazer
[exit 0]

export HISTCONTROL=ignoreboth
export HISTSIZE=5000
# Tema default (bash): usuário@host:pasta
PS1='\[\e[32m\]\u@\h\[\e[0m\]:\[\e[34m\]\w\[\e[0m\]\$ '
# <<< ryx <<<
```
