# Carta de engenharia

Vale para qualquer pessoa ou agente (Claude, Gemini, humano) que mexa neste repositório. Texto original do
mantenedor, em inglês, 20/10/2026; esta é a versão de trabalho.

## Missão

Um toolkit real, seguro, modular e aberto para personalizar o Termux, administrar serviços no Android,
automatizar tarefas suportadas e integrar agentes de IA que já existem.

Tem de ser implementado, executado, testado e documentado. Proposta de arquitetura, arquivo gerado, saída
simulada ou "o código compilou" **não** contam como recurso pronto.

## Regras obrigatórias

1. Inspecione o repositório, o ambiente do aparelho, as dependências instaladas e o estado atual antes de mudar.
2. Preserve o que funciona. Não troque uma implementação sem entender dependências e comportamento.
3. Núcleo primeiro: detecção de ambiente, validação de config, log estruturado, CLI, estado, backup e rollback seguro.
4. Componentes modulares com interface, dependências, capacidades e comportamento de falha explícitos.
5. Núcleo leve: recursos opcionais (servidor, IA) nunca viram dependência obrigatória da instalação básica.
6. Termux **sem root** é o padrão. Detecte o que não é suportado em vez de fingir sucesso.
7. Consentimento explícito para ação destrutiva, exposição de rede pública, mudança de permissão sensível ou
   instalação de ferramenta externa opcional.
8. Simulação de verdade: sem `--apply` nada muda (arquivo, pacote, serviço ou estado do sistema).
9. Registre as mudanças e restaure só arquivos gerenciados pelo toolkit. Preserve dados do usuário e dependências compartilhadas.
10. Nunca: segredo no código, resultado de teste inventado, exceção engolida ou capacidade que não existe.
11. Não execute script de instalação não confiável nem rode sozinho comando sugerido por agente de IA externo.
12. Dependências fixadas ou controladas de forma reprodutível; valide config e caminhos; audite atualizações.
13. Documentação, ajuda da CLI, notas de versão e comportamento real sempre iguais.

## Fluxo de entrega (por recurso)

1. Inspecionar o que existe e escrever os critérios de aceite.
2. Desenhar interface, dependências, modos de falha e estratégia de rollback.
3. Implementar a menor fatia vertical completa.
4. Testes unitários, de integração e de segurança relevantes.
5. Rodar os testes e registrar os códigos de saída e resultados **reais**.
6. Verificar num Termux suportado quando o recurso depende de Android ou Termux.
7. Revisar regressões, permissões, logs, segredos e mudanças no sistema de arquivos.
8. Atualizar a documentação e listar os arquivos alterados.
9. Só marcar pronto quando os critérios de aceite forem cumpridos.

## Definição de pronto

Implementação existe, testes **rodaram**, comportamento esperado verificado, falha verificada, documentação
atualizada, limitações declaradas. Se faltar aparelho, serviço, permissão ou dependência para um teste, ele é
**BLOCKED** ou **NÃO VERIFICADO**. Resultado simulado nunca substitui verificação em aparelho real.

## Relatório de cada marco

- recursos implementados e arquivos alterados;
- comandos realmente executados;
- testes que passaram, falharam, foram pulados ou ficaram bloqueados;
- achados de segurança e regressões;
- compatibilidade verificada em aparelho real;
- limitações conhecidas e o que falta;
- próximos passos exatos para a próxima versão.

Correção, segurança, manutenção e resultado reproduzível valem mais que volume de código.
