# KRAKEN MESH v2.0 — diretiva de engenharia (resumo de trabalho)

Texto original do mantenedor, em inglês, 20/10/2026. Amplia a [EDGEWARD](EDGEWARD.md) (camadas, risco L0–L3,
ciclo de transação, manifesto de mudanças): o que está lá continua valendo e não é repetido aqui.
**Proposta, não implementação.** Nome, CLI (`krakenmesh`) e repositório (`kraken-mesh`) são candidatos; o
pacote segue `ryx` até a validação de nome (seção 2.2) e uma ADR registrar a troca.

As seções 18–27 (roteiro das fases 0–8, pronto-quando, portões, instalador, observabilidade, automação, protocolo multiagente, repositório público, MVP) chegaram depois: [KRAKEN_MESH_v2.1.md](KRAKEN_MESH_v2.1.md).

Lema: *muitos aparelhos, um enxame, suas regras.*

## Missão

Juntar o hardware pessoal (celulares velhos com Termux, o celular do dia a dia sob política conservadora,
aparelhos mais fortes, PCs quando houver) num conjunto coordenado que roda tarefas e agentes de IA **sem VPS
pago, sem servidor na nuvem permanente e sem API comercial obrigatória**. Continua útil sem internet, com um
nó caindo, com provedor fora do ar e com um único aparelho.

Tem de ser sistema distribuído de verdade, não um painel mandando SSH para uma máquina só.

## Princípios (valem acima da quantidade de recursos)

1. **Sem infraestrutura paga obrigatória.** Nada de plano de controle na nuvem, banco pago, fila hospedada,
   telemetria ou relay do desenvolvedor no núcleo. GitHub só distribui; o runtime instalado roda sem ele.
2. **Custo honesto.** Gasto máximo padrão com API de IA: **€0,00**. Valor maior só com configuração explícita.
   Tarefa nunca troca sozinha para provedor pago quando o local ou o gratuito falha. Nunca contornar paywall,
   cota, autenticação ou termos de provedor.
3. **Local primeiro.** Estado nos aparelhos do usuário; queda de rede não corrompe nada; nada sobe para
   terceiros por padrão.
4. **Hardware velho com critério.** Celular fraco faz checagem, hash, backup, script pequeno e fila; não é
   forçado a rodar modelo grande.
5. **Celular do dia a dia protegido.** Carga pesada desligada por padrão; limites de bateria, temperatura,
   memória, carregamento, dados móveis, uso em primeiro plano e horário de silêncio, até onde o Android expõe.
   Nada de consumir recurso escondido nem agir como minerador.
6. **Prova acima da aparência** (mesma definição de pronto da carta).

## Modos

- **Standalone** é a base, não demo: cada aparelho se inspeciona, executa, guarda config e fila sozinho.
- **Mesh**: pareamento, identidade, anúncio de capacidades, saúde, alocação, resultado, cancelamento, falha e
  replicação controlada. Rede local primeiro; acesso remoto opcional; nada administrativo exposto à internet.
  Quando NAT ou operadora impedirem conexão direta, detectar e explicar.
- **Coordenador** é papel de um aparelho pareado, não servidor fixo. Documentar quais tarefas exigem
  coordenador ativo; recuperação de coordenador só com projeto de transição de estado provado. Não afirmar
  "sem ponto único de falha" sem teste de injeção de falha.

### Estados de tarefa

`CREATED → VALIDATED → QUEUED → LEASED → RUNNING → VERIFYING → SUCCEEDED`, mais `FAILED`, `CANCELLED`,
`BLOCKED`, `EXPIRED`, `RETRY_PENDING`, `NEEDS_RECONCILIATION`. Sem promessa de "exatamente uma vez". Efeito
colateral exige chave de idempotência, lease, retry limitado e reconciliação; sem replay seguro, revisão humana.

## Capacidades do aparelho

Papéis combináveis: `CONTROL`, `WORKER`, `INFERENCE`, `STORAGE`, `DAILY_PHONE`, `DESKTOP_BRIDGE`. Estados:
`SUPPORTED`, `UNSUPPORTED`, `UNKNOWN`, `TEMPORARILY_UNAVAILABLE`, `NEEDS_CONFIGURATION`, cada um com
**frescor**. Compatível não é o mesmo que útil. Sem sensor ou permissão, relatório básico, nunca dado inventado.

## Agendador

Cada tarefa declara runtime, memória, disco, CPU e duração, modelo e contexto, rede, sensibilidade dos dados,
onde pode rodar, prioridade, prazo, retries, custo, limites de bateria e temperatura, se é idempotente e se
pode ser dividida. Ordem de critério: segurança e permissão → capacidade → privacidade → recurso estimado →
proteção do celular pessoal → tempo → transferência → fila → reuso de modelo → energia → orçamento →
confiabilidade recente. `scheduler explain` mostra por que um nó foi escolhido ou excluído.

Classes: A operações locais · B workers leves · C desenvolvimento · D inferência local · E IA conectada
(opcional) · F longa duração com checkpoint. Dividir só o que é separável; inferência distribuída entre
celulares fica experimental até prova.

## IA

Adaptador neutro de provedor; local primeiro quando serve. Modelo local: checar memória e disco, estimar antes
de baixar, download verificado, nunca baixar modelo enorme ou ligar inferência pesada no celular pessoal sem
confirmação, nunca empacotar pesos. Adaptadores (Codex CLI, Claude Code, Hermes, runtimes abertos) só depois de
ler a documentação oficial; `VERIFIED` só com execução real; matriz de compatibilidade com plataforma, versão,
credencial, custo e evidência. Saída de modelo é entrada não confiável: o agente propõe ação tipada que passa
pela política, nunca shell livre.

## Segurança

- `docs/THREAT_MODEL.md` **antes** de qualquer recurso de mesh em aparelho real.
- Domínios de confiança separados: operador, interface local, cada nó, workers e plugins, agentes, provedores,
  artefatos baixados, rede local, transporte remoto. Estar no mesmo Wi-Fi não autoriza nada.
- Pareamento: identidade criptográfica gerada no aparelho, confirmação do usuário, impressão digital da chave,
  capacidades por par, revogação, rotação; QR sem segredo de longa duração reutilizável.
- Transporte: TLS com autenticação mútua ou protocolo revisado equivalente. **Proibido inventar criptografia.**
  Controle em loopback por padrão.
- Capacidades granulares e nega por padrão (`system.read_basic`, `filesystem.read_scoped`,
  `task.execute_declared`, `service.restart_managed`, `model.invoke_local`, `provider.invoke_configured`,
  `node.pair`, `node.revoke`…), sem curinga.
- Execução: lista de argumentos, caminho canonizado, symlink tratado, cwd restrito, env por lista permitida,
  timeout, saída limitada. Sem sandbox real no Android, declarar a fronteira mais fraca.
- Sem acesso a fotos, contatos, SMS ou chamadas no núcleo.
- Auditoria por evento; cadeia de hash ajuda, mas log local não é "à prova de adulteração".

## Android e Termux

Distinguir tarefa em primeiro plano, de fundo (melhor esforço), no boot, serviço supervisionado e longa com
checkpoint. Nunca prometer 24/7. Bash e Zsh detectados à parte; `.bashrc`/`.zshrc` preservados com backup.
Nunca prometer aceleração, RAM extra, fuga do limite térmico ou root automático.

## Perfis

`personal` (conservador, sem boot automático) · `worker` (concorrência limitada, logs e cache limitados) ·
`dedicated` (só com configuração explícita) · `inference` (memória do modelo antes de carregar). Ficar muito
tempo online não torna um aparelho "dedicado".

## Instalação, CLI, painel

Modos: mínimo, por módulo, completo, só auditoria, checar atualização, simulação, recuperação. Desinstalar só o
que é do toolkit, com simulação. CLI primeiro (`doctor`, `info`, `status`, `node`, `mesh`, `task`,
`scheduler explain`, `models`, `agents`, `backup`, `update --check`, `uninstall --dry-run`); cada comando
só quando existir e tiver teste. Painel depois, em loopback, com a mesma política; todo dado marcado `VERIFIED`,
`STALE`, `UNAVAILABLE`, `UNSUPPORTED` ou `UNKNOWN`, com hora e fonte; medida ausente nunca vira verde.

## Testes exigidos além da carta

Falhas distribuídas: worker some antes ou durante a tarefa, coordenador morre, partição de rede, mensagem
duplicada, lease vencido, relógios diferentes, nó volta com estado velho, envio repetido, efeito não
reexecutável, resultado depois do lease, pareamento duplo, revogação de nó desconectado, mensagem malformada,
celular fraco sem recurso. Segurança: pareamento não autorizado, replay de credencial, nó revogado voltando,
escalada por argumento de plugin, fallback pago não aprovado. Fixture simulada nunca se passa por aparelho.

## Fase 0 (a única liberada agora)

Inspecionar o ambiente e o que já funciona, limites do hardware e do Termux, modelo de ameaças, **validação do
nome** (GitHub, PyPI, npm, domínios, produtos, marcas; se houver conflito, 5 alternativas), ADRs, critérios de
aceite e backlog com dependências. Saída: achados com evidência, decisões documentadas e a primeira fatia
identificada.
