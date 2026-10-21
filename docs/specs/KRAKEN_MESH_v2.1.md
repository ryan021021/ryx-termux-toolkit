# KRAKEN MESH v2.1 — continuação (seções 18–27, resumo de trabalho)

Texto original do mantenedor, em inglês, 20/10/2026. Continua a [v2.0](KRAKEN_MESH.md) e a [EDGEWARD](EDGEWARD.md),
que seguem valendo. **Proposta, não implementação.** Comandos `krakenmesh ...` e `python -m pytest` são alvos, não
coisas que já existem. Nome do pacote segue `ryx` até a ADR de nome.

## 18. Roteiro (cada fase só abre quando a anterior cumpre a saída)

| Fase | Entrega | Critério de saída |
|---|---|---|
| 0 Auditoria | git, arquitetura, dependências, ambiente (SO, Python, shell, arquitetura, Termux), reaproveitáveis, falhas, docs oficiais de integrações, limites do aparelho, ADRs | linha de base reproduzível, achados, modelo de ameaças, matriz de compatibilidade, plano aprovado |
| 1 Runtime local | CLI, config validada, detecção de capacidade, fila persistente, máquina de estados, log estruturado com redação, diagnóstico só leitura, política de execução, manifestos de instalar/remover, testes unitários e de CLI | instala, inicia, roda tarefa limitada (ex.: validar config, checksum), persiste e se recupera após reinício do processo |
| 2 Malha de 2 aparelhos | identidade, pareamento explícito, comunicação autenticada, troca de capacidades, envio/resultado, heartbeat e nó velho, revogação, fila offline, diagnóstico de conexão | dois aparelhos **reais** trocam tarefa com segurança; nó fora do ar não corrompe tarefa calado (simulação não substitui) |
| 3 Agendador | elegibilidade por recurso, privacidade/permissão, bateria e temperatura quando mensuráveis, prioridade, retry limitado, lease, explicação da escolha, medida desconhecida tratada como desconhecida | testes provam rejeição de nó incompatível ou sem permissão e escolha conforme a política |
| 4 Adaptadores de IA | um por vez: executor determinístico → inferência local → uma integração de agente verificada → outras só com caso de uso | cada adaptador passa no teste de contrato; indisponível é reportado como indisponível |
| 5 Termux/Android | detecção, perfis de pouca memória, boot opcional, interrupção segura, armazenamento e bateria, diagnóstico Android, testes de instalar/remover e em aparelho real | funciona nos ambientes listados e testados; nada de "todo Android" |
| 6 Confiabilidade | lease persistente, reconciliação, idempotência, checkpoint, backup/restauração, recuperação do coordenador, injeção de falha, autocura limitada | cenários de falha suportados passam de forma repetível, inclusive perda do coordenador e queda de rede |
| 7 Painel | mesmas interfaces autenticadas da CLI: aparelhos, histórico, aprovações, capacidades, políticas, logs, compatibilidade | ação do painel = mesma permissão da CLI; todo status tem fonte real ou aparece "desconhecido" |
| 8 Lançamento | docs de instalação, SECURITY, modelo de ameaças, arquitetura, CONTRIBUTING, licença, CHANGELOG, checagens reproduzíveis, artefatos com integridade, remoção e recuperação testadas | checklist completo, limitações documentadas, portões passando |

Não reescrever componente que funciona só porque outro agente prefere outra arquitetura.

## 19. Pronto quando
Existe no repositório; interface pública documentada; entrada/saída validadas; sucesso e falha testados; permissão
testada; limite de recurso aplicado; erro acionável; log sem segredo; instalação/remoção entendidas; limites de
compatibilidade escritos; testes **rodados**; resultado observado = documentado; sem dependência de nuvem escondida;
sem contornar consentimento ou regra de provedor.
- Estado distribuído: + desconexão, entrega duplicada, reinício, dono de tarefa velho.
- IA: + credencial ausente, rate limit, vazamento para fora, proibição de fallback pago automático.
- Instalador: + interrupção, config preexistente do usuário, conflito de rollback, remover só o que é gerenciado.
Arquivo de teste gerado não é teste passado; checagem de sintaxe não é integração; mock não é Android real.

## 20. Portões automáticos
Estados de resultado: **PASS** (rodou e cumpriu), **FAIL** (rodou e achou defeito), **BLOCKED** (pré-requisito
ausente), **NOT RUN**, **NOT VERIFIED**. Lançamento nunca converte os três últimos em PASS. CI nas plataformas de
host; testes Android/Termux em aparelho real ou marcados indisponíveis. Sem dependência nova sem justificativa.

## 21. Contrato do instalador (sensível)
Faz: detecta SO/shell e suporte, confere pré-requisitos, mostra o plano, valida origem e integridade, pede aprovação
antes de mudança grande, faz backup do que altera, aplica em transação quando possível, confere a versão, grava o
manifesto, dá instrução de rollback.
Não faz: exigir root no Termux básico; instalar modelo ou dependência grande calado; sobrescrever config de shell sem
consentimento; `curl | sh` sem revisão; desligar proteção do Android; serviço de boot escondido; porta pública por
padrão; credencial no repositório; prometer rollback do que não volta.
Remoção: só o que é do projeto (pelo manifesto), nunca dado do usuário nem dependência compartilhada; `--dry-run` lista
antes; conflito com mudança posterior do usuário → conservador.

## 22. Observabilidade
O operador precisa saber: pareados, alcançáveis, capacidades verificadas, tarefas (fila/rodando/bloqueadas), qual nó
executa e por quê, modelo local ou externo, se pode haver gasto, se precisa aprovação, o que houve na última falha, o
que muda num update/remoção, se a informação está atual.
Severidade: `INFO NOTICE WARNING ERROR CRITICAL`. Estado: `HEALTHY DEGRADED OFFLINE BLOCKED UNKNOWN`. Último heartbeat
bom não torna nó offline "saudável". Funciona em terminal sem cor e em tela pequena.

## 23. Automação com orçamento
Cada automação declara (contrato ilustrativo): `enabled=false`, `max_attempts`, `cooldown_seconds`,
`max_runtime_seconds`, `allow_cellular_data=false`, `require_charging`, `require_confirmation`; todo campo validado.
Runtime sabe pausar, cancelar com segurança, parar de agendar, drenar worker, retomar, explicar a pausa, impedir laço
de falhas e guardar estado para investigação. Recuperação = retry limitado + pós-condição conferível. Agente de IA não
altera as próprias políticas para escapar de limite.

## 24. Protocolo multiagente
1. Agente líder faz a linha de base (repo, dependências, testes, git) e o mapa da arquitetura.
2. Contratos antes do paralelo: tarefa, capacidades, decisão de autorização, mensagens, agendador, estado persistido,
   adaptador de agente, erro.
3. Divisão: cada agente com subsistema, arquivos próprios e critério mensurável; branch/worktree separados; sem
   edição simultânea descoordenada em arquivo central.
4. Revisão independente: segurança ataca o diff real; engenheiro de testes roda os testes; o líder só integra com
   evidência.
5. Conflito: comparar requisito, segurança, compatibilidade, evidência, manutenção, recurso, simplicidade, nunca a
   confiança de quem fala.
6. Relatório com evidência: `Task / Files changed / Implementation status / Commands executed / Tests passed / Tests
   failed / Tests blocked / Known limitations / Security implications / Integration dependencies / Next action`.
   Nunca inventar saída. Fatia vertical testada > volume de código.

## 25. Repositório público
Explicar: o que faz e o que não faz, plataformas, execução local, pareamento, permissões, instalar/remover, reproduzir
testes, reportar vulnerabilidade, contribuir, efeito de provedor externo em privacidade e custo. Licença após conferir
distribuição e obrigações. Exemplos sanitizados (sem credencial, IP privado, identificador de aparelho, caminho de
usuário). CI pública sem token pessoal, permissões mínimas, actions revisadas, sem rodar PR não confiável com
privilégio. Útil sem telemetria, conta ou serviço hospedado.

## 26. Teste de aceitação do MVP (16 passos)
1 instalar num aparelho sem VPS · 2 diagnóstico com relatório de capacidade correto · 3 tarefa local limitada ·
4 reiniciar e recuperar o histórico · 5 parear 2º aparelho · 6 conferir identidade e permissões · 7 enviar tarefa pela
LAN · 8 receber e validar o resultado · 9 desligar o worker no meio · 10 estado correto e retry seguro ·
11 tarefa incompatível rejeitada · 12 par revogado não reconecta · 13 pedido a modelo externo com provedores
desligados é rejeitado · 14 logs sem segredo · 15 testes de instalar/remover · 16 suíte automática com resultado
publicado. Marcar o que foi verificado em aparelho real e o que está BLOCKED. Sem o caminho real de pareamento e
execução, não lançar como runtime distribuído.

## 27. Ordem final
Auditar → restrições e o que existe → modelo de ameaças e interfaces → runtime local → testes → 2 aparelhos →
agendador → modelos/agentes seletivos → Termux/Android → recuperação → painel → instalar/remover/lançar → publicar só
o que tem evidência. Não parar na documentação se a tarefa pede implementação; não fazer todas as fases numa mudança
só; após cada fatia, testar, revisar o diff e atualizar a doc. Impossível no hardware → explicar e dar a alternativa
segura. Dependência/credencial ausente → BLOCKED, nunca simular sucesso. Preservar implementação melhor que já exista.

Cobertura no repositório, seção por seção: [COBERTURA_v2.1.md](COBERTURA_v2.1.md).
