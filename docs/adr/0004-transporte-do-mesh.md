# ADR-0004 — Transporte e identidade do mesh pelo OpenSSH

Estado: PROPOSTA. Exige revisão de segurança independente antes de virar código, e nada de mesh roda em
aparelho real antes do [modelo de ameaças](../THREAT_MODEL.md) estar aceito.

## Contexto

A diretiva proíbe criptografia caseira e pede identidade gerada no aparelho, pareamento confirmado pelo
usuário, impressão digital, revogação e transporte autenticado. A biblioteca padrão do Python faz TLS, mas
**não gera** chave nem certificado; o A15 não tem `openssl` no PATH (F6). O OpenSSH já está no Termux, roda
sem root e é um protocolo revisado.

## Opções

| Opção | Prós | Contras |
|---|---|---|
| A. OpenSSH (`ssh-keygen` ed25519, `authorized_keys` com `command=` e `restrict`) | já instalado; impressão digital padrão; revogação = tirar a linha | um processo `ssh` por chamada; precisa de sshd em cada nó que recebe tarefa |
| B. TLS mútuo com `ssl` + `openssl` para gerar certificados | conexão persistente | depende de binário ausente; gestão de CA própria |
| C. TLS mútuo com o pacote `cryptography` | API completa | dependência nativa pesada no Termux; contraria ADR-0001 no núcleo |

## Decisão proposta

Opção A para o mesh v1: identidade = par ed25519 do ryx (separado da chave pessoal do usuário); pareamento =
mostrar e confirmar a impressão digital nos dois aparelhos; autorização = linha em `authorized_keys` com
`restrict,command="ryx node rpc"`, que aceita só mensagens tipadas e valida tudo pela política (ADR-0002).

## Consequências

- Nenhum shell livre pelo mesh: o `command=` forçado ignora o comando pedido pelo par.
- O sshd do nó passa a ser parte da superfície de ataque do ryx; escuta, senha e chaves precisam de checagem
  no `doctor` (relaciona-se ao achado F7).
- Reavaliar B ou C se a latência por chamada inviabilizar o agendador.
