# Fase 0 — inventário, achados e validação de nome (20/10/2026)

Referências: [EDGEWARD](EDGEWARD.md), [KRAKEN MESH](KRAKEN_MESH.md), [carta](../ENGINEERING_CHARTER.md).
Tudo aqui foi medido nos comandos da última seção; o que não foi medido está marcado.

## 1. Inventário

### Repositório

| Item | Estado |
|---|---|
| Git | `main` **sem nenhum commit** (todo o trabalho só existe no disco) |
| Pacote | `ryx` 0.1.0, `requires-python >=3.11`, só biblioteca padrão |
| Código | `src/ryx/`: `cli`, `config`, `paths`, `platform`, `permissions`, `backup`, `state`, `logger`, `registry` e 6 módulos (`shell`, `diagnostics`, `packages`, `server`, `automation`, `ai`) |
| Testes | `tests/unit`, `integration`, `installer`, `security` (~4 980 linhas de Python e shell no total) |
| CI | 3 workflows escritos, **nunca rodaram** (sem remoto) |
| Mesh, pareamento, agendador, inferência | **não existem** (só especificação) |

### Máquina de desenvolvimento

Windows 11, Git Bash, Python 3.14.0, git 2.53. Não é Android: nada medido aqui vale como prova no aparelho.

### Aparelho conectado (A15)

Lido por ADB e por SSH via `adb forward`, só leitura; a impressão digital da chave do sshd confere com o perfil.

| Item | Valor medido |
|---|---|
| Modelo / Android | SM-A156B, Android 16 (SDK 36), patch 2026-07-05 |
| CPU | arm64-v8a (`aarch64`), 8 núcleos |
| RAM | 3,6 GB no total; ~0,95 GB disponível no momento da leitura |
| Armazenamento | 73 GB livres de 105 GB |
| Bateria | 100 %, USB, 29 °C (`termux-battery-status` funciona) |
| Termux | 0.118.1, com `com.termux.boot` e `com.termux.api` |
| Ferramentas | `bash`, `git`, `runit` (`sv`, `runsvdir`), `termux-wake-lock`, `crontab`; **sem `python`**, sem `zsh`, sem `openssl` no PATH |
| Serviços runit | `agentops`, `alertas`, `crond`, `egress`, `server-box`, `sftp`, `ssh-agent`, `sshd` (do projeto `celular`) |
| `/proc/loadavg` | permissão negada (limite do Android) |

## 2. Achados por gravidade

| # | Gravidade | Achado | Consequência |
|---|---|---|---|
| F1 | ALTA | Repositório sem commit | Sem histórico, sem volta; uma limpeza errada apaga tudo. Commit-base é a T96. |
| F2 | ALTA | Python ausente no Termux do A15 | O ryx **não roda** no único aparelho disponível sem `pkg install python`. Instalar exige consentimento (regra 7). Teste no aparelho: BLOCKED. |
| F3 | ALTA | Nada foi verificado em aparelho | Toda afirmação de compatibilidade é NÃO VERIFICADO. |
| F4 | MÉDIA | `/proc/loadavg` negado; CPU e carga não saem por `/proc` | Detector de saúde precisa marcar UNSUPPORTED/UNKNOWN em vez de zero. |
| F5 | MÉDIA | RAM disponível < 1 GB | Pelo perfil KRAKEN, este aparelho é `worker`, não `inference`; inferência local fica UNKNOWN até medir um modelo. |
| F6 | MÉDIA | `openssl` ausente | Identidade e TLS do mesh não podem depender do binário `openssl`; ver ADR-0004. |
| F7 | MÉDIA | sshd do `celular` sem `ListenAddress` nem `PasswordAuthentication` explícitos no `sshd_config` (valor efetivo não lido: `sshd -T` falhou) | Fora do escopo do ryx; reportado ao projeto `celular` (BACK/QA). NÃO VERIFICADO. |
| F8 | BAIXA | CI nunca rodou | Lint e testes em Linux/macOS sem prova. Depende de remoto (decisão do mantenedor). |

## 3. Validação do nome "KRAKEN MESH"

| Verificação | Resultado |
|---|---|
| PyPI `krakenmesh`, `kraken-mesh` | livres (404) |
| npm `krakenmesh`, `kraken-mesh` | livres (404) |
| GitHub usuário/org `krakenmesh`, `kraken-mesh` | livres (404) |
| GitHub repositórios "kraken mesh" | 3; um é um framework de C2 "OPSEC-first" chamado Kraken e outro um chat em malha |
| GitHub "kraken" | ~11 900 repositórios; `uber/kraken` (6,7 mil estrelas) é distribuição P2P, **mesmo domínio técnico** |
| PyPI/npm `kraken` | ocupados |
| Marcas | **NÃO VERIFICADO** (sem consulta a INPI, EUIPO ou USPTO). "Kraken" é marca conhecida de corretora de cripto, de gateway de API (KrakenD), de cliente git (GitKraken) e de hardware |

Veredito: identificadores exatos livres, mas **conflito material provável** (mesmo domínio que `uber/kraken`,
marca forte de cripto e associação com ferramenta de C2, o que vai contra o "não é para operação encoberta").
Pela seção 2.2 da diretiva, cinco alternativas, conferidas do mesmo jeito (PyPI, npm e nomes de repositório
no GitHub, todos livres em 20/10; marcas NÃO VERIFICADO):

| Nome | História |
|---|---|
| **cephalomesh** | Cefalópode: o polvo tem um cérebro central e gânglios em cada braço que decidem sozinhos; é o modelo standalone + mesh. |
| **reefmesh** | Recife: estrutura viva construída sobre peças antigas; aparelhos aposentados viram base de algo útil. |
| **shoalmesh** | Cardume: muitos indivíduos pequenos que se movem juntos sem chefe fixo; coordenador é papel, não servidor. |
| **polypmesh** | Pólipo: cada um é simples, a colônia é forte; celular fraco contribui com tarefa leve. |
| **ninebrain** | O polvo tem nove "cérebros"; 3 repositórios pequenos com o nome (0–3 estrelas), conflito baixo. |

Decisão de nome é do mantenedor; enquanto isso o pacote segue `ryx` (ADR-0005).

## 4. Comandos executados

```text
python --version; git --version; git status -sb            # 3.14.0, 2.53, "No commits yet on main"
find src tests scripts ... | xargs wc -l                   # tamanhos acima
adb devices -l; adb shell getprop ...                      # modelo, Android, ABI
adb shell "grep Mem /proc/meminfo; df -h /data; dumpsys battery; pm list packages | grep termux"
adb forward tcp:18022 tcp:8022; ssh -p 18022 ...           # uname, python, termux-info, command -v, df
ssh ... 'grep sshd_config; termux-battery-status; nproc; ls $PREFIX/var/service; cat /proc/loadavg'
ssh ... 'sshd -T'                                          # saída 1, sem resultado
curl pypi.org/pypi/<nome>/json; curl registry.npmjs.org/<nome>; curl api.github.com/search/repositories
```

## 5. Próximo marco verificável

1. Commit-base (T96) com a suíte rodada no Windows.
2. Com o OK do mantenedor: `pkg install python` no A15 e a suíte rodada lá (T97), com códigos de saída reais.
3. Fase 1 (standalone) a partir do backlog da T103, começando por capacidades com estado e frescor (ADR-0003).
