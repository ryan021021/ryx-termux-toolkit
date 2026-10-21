# EDGEWARD — diretiva de engenharia (resumo de trabalho)

Texto original do mantenedor, em inglês, 20/10/2026. Amplia a [carta de engenharia](../ENGINEERING_CHARTER.md);
em conflito, vale a regra mais restritiva. **Nome provisório**: o pacote continua `ryx` até a checagem de
nome e marca; nada é renomeado sem decisão do mantenedor.

Lema: *toda ação tem um limite; todo resultado tem prova.* O valor central é a **execução controlada**: cada
operação tem escopo, regra de autorização, verificador de resultado e estratégia de falha.

Não é: um sistema operacional novo, um "VPS no bolso", milagre de kernel nem shell livre exposto a IA.

## Camadas (dependência só para baixo)

| Camada | Conteúdo | Hoje no ryx |
|---|---|---|
| A Plataforma | Termux, arquitetura, shell, Python, caminhos, root (sem escalar), PRoot, add-ons, pkg | `platform.py`, `paths.py` (parcial) |
| B Núcleo | CLI, registro de comandos, esquema de config, registro de módulos, erros, estado | `cli`, `config`, `registry`, `state` |
| C Política | capacidades explícitas, nega por padrão, classes de risco L0–L3, aprovações, limites, revogação | `permissions.decide` (só simulação/`--apply`/`--yes`) |
| D Transação | plano, simulação real, pré/pós-condições, timeout, cancelamento, registro e recuperação | `backup` (parcial); falta manifesto de mudanças |
| E Módulos | shell, diagnóstico, pacotes, serviços, automação, backup, IA opcional | `modules/` |
| F Interfaces | CLI primeiro; TUI depois; painel local só com núcleo e testes de segurança prontos | só CLI |
| G Release | CI, análise de segurança, manifesto, checksums, matriz de compatibilidade, changelog | workflows (nunca rodaram) |

Nenhum agente de IA, painel ou plugin passa por fora das camadas C e D.

## Ciclo de toda mudança de estado

`DISCOVER → PLAN → VALIDATE → AUTHORIZE → BACK UP → EXECUTE → VERIFY → RECORD`

Cada tarefa tem id, estado inicial, operações propostas, decisão da política, saída, estado final e evidência.
Se a verificação falhar: para o que depende dela, guarda diagnóstico seguro, decide se dá para voltar, só
recupera o que estiver autorizado e declara recuperação incompleta.

## Risco

| Classe | O que é | Regra |
|---|---|---|
| L0 | leitura | automática dentro do escopo concedido |
| L1 | ação pequena e limitada | automática só com política específica e limites aplicados |
| L2 | mudança reversível | plano revisável, backup e aprovação |
| L3 | destrutiva, privilegiada, exposta à rede ou com credencial | negada ou aprovada por humano; nunca pela confiança do modelo |

A aprovação fica presa à operação, aos argumentos, ao alvo e à versão do plano: mudou argumento sensível,
perde a validade. Agente não aprova a própria ação perigosa. Verificador que falha bloqueia o "pronto".

## Manifesto de mudanças (fora do checkout)

Arquivos criados e alterados, cópia original ou referência de backup, hash esperado, pacotes pedidos pelo
toolkit, serviços e jobs iniciados, módulos ativados, estado da restauração e conflitos com mudanças do
usuário. Antes de restaurar, confere se o usuário mexeu depois; não sobrescreve sem avisar. Desinstalar só o
que é comprovadamente do toolkit; dependência compartilhada nunca sai sozinha.

## Capacidades do ambiente

`SUPPORTED`, `UNSUPPORTED`, `UNKNOWN` ou `NEEDS_CONFIGURATION`. Pacote presente não prova recurso
funcionando. Perfis de aparelho viram fixtures; compatibilidade com aparelho só com teste no aparelho.

## Módulos-alvo

M01 shell · M02 doctor · M03 pacotes · M04 serviços · M05 automação · M06 backup · M07 rede (só local; bind
público, túnel ou acesso remoto exigem revisão de segurança própria) · M08 adaptadores de IA (matriz de
capacidades explícita) · M09 observabilidade · M10 atualização com integridade e caminho de volta.

## Fases

P0 auditoria, modelo de ameaças, contrato de compatibilidade e requisitos · P1 núcleo, CLI, config, log e
detecção · P2 política, registro tipado, simulação e transações · P3 instalador, manifesto, backup e
desinstalador · P4 shell, diagnóstico e pacotes · P5 serviços, automação limitada e recuperação · P6
adaptadores de agente e gateway restrito · P7 TUI e painel local opcional · P8 testes adversariais, aparelho,
release e docs públicas. Uma fase por vez; candidato a release funcionando ao fim de cada marco.

## Primeira entrega exigida (P0)

1. Inventário do ambiente e do repositório.
2. Achados por gravidade.
3. Modelo de ameaças e fronteiras de confiança (`docs/THREAT_MODEL.md`).
4. ADRs das escolhas principais (`docs/adr/`).
5. Backlog priorizado com dependências.
6. Primeira fatia vertical com código e testes reais.
7. Comandos executados e resultados.
8. Bloqueios, limitações e próximo marco verificável.

## Identidade visual (quando o nome for confirmado)

Preto `#070A0D`, lima `#A3FF12`, ciano `#53D9FF`, texto apagado `#94A39A`. Escudo ou portal angular com cursor
de terminal no espaço negativo e três nós ligados (config, serviços, automação). SVG original, versão
monocromática, marca ASCII e ícone. Status verde nunca sugere segurança que não foi provada.
