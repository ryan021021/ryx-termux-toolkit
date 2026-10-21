# Cobertura da KRAKEN MESH v2.1 no repositório (21/10/2026)

Cada seção da [v2.1](KRAKEN_MESH_v2.1.md) contra o que existe. Fonte: `grep` em `src/`, `docs/`, `install.sh`,
`uninstall.sh` e `.github/`. Ter o arquivo não é ter passado no teste: tudo aqui é **NOT VERIFIED** até rodar.

| § | Tema | Já existe | Falta |
|---|---|---|---|
| 18 F0 | Saída da fase 0 | linha de base e achados (`FASE0.md`), `THREAT_MODEL.md`, ADR-0001…0005 | **matriz de compatibilidade** (nenhum arquivo); **plano aprovado** pelo mantenedor (T103 em REVIEW) |
| 18 F1 | Runtime local | CLI (`cli.py`), config (`config.py`), log com redação (`logger.py`), estado (`state.py`), manifesto de backup (`backup.py`), install/uninstall com `--dry-run` | **fila persistente de tarefas e máquina de estados** (nenhum `queue`); tarefa limitada de exemplo (checksum/validar config); teste de recuperação após reinício. T104–T107 cobrem só capacidades, risco, sshd e fixtures |
| 18 F2–F8 | Malha, agendador, IA, Android, confiabilidade, painel, lançamento | ADR-0004 (transporte) | tudo; correto, porque só abrem depois da F1 |
| 19 | Pronto quando | `ENGINEERING_CHARTER.md` | levar a lista (estado distribuído, IA, instalador) para o checklist de revisão das tarefas ryx |
| 20 | Portões e estados PASS/FAIL/BLOCKED/NOT RUN/NOT VERIFIED | carta usa os estados; CI `lint`, `tests`, `security` | CI **nunca rodou** (F8, sem remoto). Suíte: 295 OK no Windows e no A15 (python 3.14.8, 21/10, T97) |
| 21 | Instalador | `install.sh`/`uninstall.sh` com dry-run, backup | conferir contra o contrato: plano antes de aplicar, integridade do que baixa, manifesto de instalação, remoção só do gerenciado, teste de interrupção |
| 22 | Observabilidade | capacidades com estado (ADR-0003, T104) | estados de **nó** `HEALTHY/DEGRADED/OFFLINE/BLOCKED/UNKNOWN` e severidades `INFO…CRITICAL` (nenhum no código) |
| 23 | Automação com orçamento | `modules/automation.py` | campos `max_attempts`, `cooldown_seconds`, `max_runtime_seconds`, `allow_cellular_data`, `require_charging`, `require_confirmation` (nenhum) |
| 24 | Protocolo multiagente | quadro do `celular` (TASKS, locks, escopo por tarefa, revisão cruzada) | modelo de relatório com `Tests blocked` / `Known limitations` nas entregas ryx |
| 25 | Repositório público | README, LICENSE, SECURITY, CONTRIBUTING, CHANGELOG, CODE_OF_CONDUCT; workflows com `permissions:` | commit-base local 90ba62e (T96), sem remoto; fica privado até ordem do mantenedor |
| 26 | MVP de 16 passos | — | passos 5–12 exigem **dois aparelhos suportados**: hoje só o A15 (o A13 morreu em 19/10). Sem 2º aparelho, esses passos ficam BLOCKED |

## Bloqueios que dependem do mantenedor
1. Aprovar o plano da fase 0 (T103).
2. Segundo aparelho para o MVP. Alternativa segura pela §27: o PC Windows como 2º nó só para desenvolvimento, sem
   contar como "aparelho real" no relatório de aceitação.

## Tarefas criadas no quadro do `celular` (21/10)
- T108 (BACK): fila persistente + máquina de estados + tarefa checksum + teste de reinício (fecha a F1).
- T109 (GEM-IDE-2): matriz de compatibilidade (`docs/COMPATIBILITY.md`) com cada linha PASS/BLOCKED/NOT VERIFIED.
- T110 (ORQ): orçamento de automação (§23) com validação de todos os campos.
- T111 (FRONT): estados de nó e severidades (§22) no `doctor`.
