# Modelo de ameaças

Versão 0 (Fase 0, 20/10/2026). Cobre o ryx standalone que existe hoje e as fronteiras do mesh proposto
([KRAKEN MESH](specs/KRAKEN_MESH.md)), que **não existe ainda**. Nada de mesh roda em aparelho real antes desta
página ter as linhas do mesh com controle e teste.

Coluna "Teste": arquivo que prova o controle, `falta` (controle sem prova) ou `—` (controle não existe).

## Ativos

Arquivos de shell do usuário (`.bashrc`, `.zshrc`) · estado e config do ryx (`RYX_HOME`) · backups · chaves de
API em variáveis de ambiente · (mesh) chave de identidade do nó e lista de pares · bateria, dados móveis e uso
do celular pessoal.

## Fronteiras de confiança

| # | Fronteira | Confiável de um lado | Não confiável do outro |
|---|---|---|---|
| B1 | CLI | operador humano no terminal | argumentos, variáveis de ambiente |
| B2 | Sistema de arquivos | árvore do `RYX_HOME` | `$HOME`, symlinks, arquivos de backup recebidos |
| B3 | Processos | o ryx | ferramentas externas (`pkg`, `sv`, CLIs de IA) e suas saídas |
| B4 | Config | esquema validado | `config/*.toml` editado à mão, `state.json` corrompido |
| B5 | Rede (mesh, futuro) | nó pareado com chave conferida | qualquer outro na mesma rede, inclusive no mesmo Wi-Fi |
| B6 | IA (futuro) | política do ryx | saída de modelo, prompt de repositório, plugin |

## Ameaças do que existe hoje

| # | Ameaça | Fronteira | Controle | Teste |
|---|---|---|---|---|
| T1 | Backup hostil escreve fora do destino (`../`, absoluto, symlink, hardlink) | B2 | `safe_relative`, `inside`, recusa de link na restauração | `tests/security/test_hostile_backup.py` |
| T2 | Injeção pela CLI (argumento vira comando) | B1, B3 | subprocess só com lista, sem `shell=True` | `tests/security/test_cli_injection.py`, `test_static_scan.py` |
| T3 | Chave de API vazando em log ou saída | B1, B3 | `logger` mascara, `ai check` nunca mostra a chave | `tests/unit/test_logger.py`, `test_ai.py` |
| T4 | Bloco do shell estraga o `.bashrc` ou age num symlink | B2 | bloco gerenciado com backup e remoção byte a byte; recusa de symlink e de rc fora do `$HOME` em correção (T96) | `tests/unit/test_shell.py` (symlink: falta) |
| T5 | Simulação que grava (`--apply` ausente e algo muda) | B1 | `decide()` | `tests/integration/test_cli.py` (falta prova por varredura do disco antes/depois) |
| T6 | `state.json` ou config corrompidos derrubam ou enganam o ryx | B4 | validação de tipos e erro claro | `tests/unit/test_state.py`, `test_config.py` |
| T7 | Corrida entre conferir e restaurar (TOCTOU) | B2 | — | — (achado aberto, T102) |
| T8 | Manifesto de backup gigante esgota memória | B2 | — | — (achado aberto, T102) |
| T9 | Ferramenta externa trava | B3 | `timeout=` obrigatório (checado por AST) | `tests/security/test_static_scan.py` |

## Ameaças do mesh (antes de qualquer código)

| # | Ameaça | Fronteira | Controle exigido | Teste |
|---|---|---|---|---|
| M1 | Aparelho estranho se pareia sozinho | B5 | pareamento só com confirmação nos dois lados e impressão digital (ADR-0004) | — |
| M2 | Par revogado volta | B5 | revogação tira a chave; teste de reconexão negada | — |
| M3 | Replay de mensagem ou de aprovação | B5 | id de tarefa único, lease, aprovação presa ao hash do plano (ADR-0002) | — |
| M4 | Par pede shell livre | B5 | `command=` forçado, só RPC tipado | — |
| M5 | Mensagem malformada derruba o nó | B5 | validação de esquema e tamanho máximo | — |
| M6 | Tarefa com efeito roda duas vezes depois de queda | B5 | idempotência, `NEEDS_RECONCILIATION` | — |
| M7 | Celular pessoal usado como worker pesado | B5 | perfil `personal` nega carga pesada por padrão | — |
| M8 | sshd do nó com senha ou escutando em todas as interfaces | B5 | `doctor` confere a config efetiva e avisa (F7) | — |

## Ameaças de IA (antes de qualquer adaptador)

| # | Ameaça | Controle exigido | Teste |
|---|---|---|---|
| A1 | Saída de modelo vira comando | agente só propõe ação tipada; política decide | — |
| A2 | Fallback silencioso para provedor pago | orçamento padrão €0,00; troca de provedor só com config explícita | — |
| A3 | Prompt de repositório baixado manda o agente agir | conteúdo externo marcado como não confiável | — |

## Fora do escopo

Atacante com root ou controle total do aparelho; apps Android maliciosos com permissões próprias; o sshd e os
serviços do projeto `celular` (só os achados que afetam o ryx entram aqui).

## Riscos aceitos (com prazo)

Nenhum. T7 e T8 estão abertos e vão para a T102 (QA).
