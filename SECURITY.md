# Política de segurança

## Versões com correção

O projeto está em `0.1.x` (experimental). Só a versão mais recente recebe correção.

## Como reportar uma vulnerabilidade

**Não abra issue pública.** Use o relato privado de vulnerabilidade do GitHub
(aba *Security* → *Report a vulnerability*) neste repositório. Enquanto o repositório for privado, avise a
pessoa que o mantém diretamente. Inclua:

- versão (`ryx --version`) e sistema (`ryx info`);
- passos mínimos para reproduzir e o impacto que você enxerga;
- se possível, uma sugestão de correção.

Metas: confirmar o recebimento em até 7 dias e dar um parecer em até 30 dias. É um projeto de uma pessoa só;
prazos podem escorregar, mas você será avisado.

## O que está no escopo

- Escrita fora da pasta de destino (restauração de backup, bloco do shell).
- Injeção de comando via argumento, config, nome de pacote/serviço/tema ou manifesto.
- Vazamento de segredo em saída, log ou backup.
- Permissões de arquivo frouxas (estado e backups devem ficar em `0600`).

Fora do escopo: ataque que já exige root no aparelho; problema do próprio Termux ou do `pkg`.

## Garantias de projeto (e como são testadas)

| Garantia | Teste |
|---|---|
| Nada grava sem `--apply`; ação sensível exige `--yes` | `tests/unit/test_permissions.py`, `tests/integration/test_cli.py` |
| Restauração nunca escreve fora do destino, nem com backup forjado | `tests/security/test_hostile_backup.py` |
| Sem `eval`/`exec`/`os.system`/`shell=True`; só biblioteca padrão | `tests/security/test_static_scan.py` |
| Chave de API nunca aparece em saída ou log | `tests/security/test_cli_injection.py`, `tests/unit/test_logger.py` |
| Argumentos hostis viram erro claro, não execução | `tests/security/test_cli_injection.py` |

Veja o modelo completo em [docs/SECURITY.md](docs/SECURITY.md).
