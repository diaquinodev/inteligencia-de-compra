# Acesso do GitHub ao BigQuery

A execução agendada (`.github/workflows/dados.yml`) precisa recriar tabelas no BigQuery.
Ela não usa chave guardada: a cada execução o GitHub emite um documento assinado dizendo
"sou o repositório tal, na branch tal", e o Google troca esse documento por uma credencial
que vale por pouco tempo (federação de identidade).

| Limite | Onde está |
|---|---|
| Só este repositório, só a branch `main` | condição do provedor de identidade |
| Criar consultas no projeto; escrever só no conjunto `compras` | papéis da conta de serviço |
| O workflow só lê o repositório | `permissions` em `dados.yml` |
| Sem configuração, o workflow não roda | `if: vars.GCP_PROVEDOR != ''` |

A configuração é feita uma vez pelo dono do projeto, com
`scripts/configurar-acesso-github.ps1`.

## Conferido em 13/10/2026

- O script rodou sem erro e o modo gratuito do BigQuery aceitou a federação de identidade.
- Execução manual na `main`: verde, 13 de 13 testes de qualidade, zero desvios em 41 valores.
- A mesma execução disparada de uma branch de teste foi recusada no login:
  `The given credential is rejected by the attribute condition.` A branch foi apagada.
- Lido de volta: a condição do provedor (este repositório, branch `main`) e o papel da conta
  de serviço (escrita só no conjunto `compras`).
- Recriar as tabelas renova o prazo de 60 dias: a expiração da tabela fato passou de
  02/12/2026 para 12/12/2026.

Não conferido: uma execução pelo agendamento (a primeira é em 19/10/2026) e uma tentativa
real da conta de serviço de escrever fora do conjunto `compras` (só a configuração foi lida).
