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

- Nem o dono do projeto consegue se passar pelo robô: a tentativa, em 13/10/2026, foi
  recusada com `Permission 'iam.serviceAccounts.getAccessToken' denied`. Só o GitHub, na
  `main` deste repositório, obtém essa identidade.

## A prova que roda toda vez

Como ninguém de fora consegue usar a identidade do robô, o teste do limite roda dentro do
próprio workflow, antes de qualquer outra coisa: `scripts/provar_limite_do_robo.py` tenta
consultar dentro de `compras` (tem de conseguir) e criar um conjunto novo no projeto (tem
de ser recusado). O projeto só tem o conjunto `compras`: sem poder criar outro, o robô não
tem onde escrever fora dele. Se a permissão for alargada por engano, a execução seguinte
fica vermelha. O resultado aparece no resumo de cada execução.

Não conferido: uma execução pelo agendamento. O agendamento passou a ser diário; a primeira
execução automática esperada é a das 09:00 UTC do dia seguinte ao merge.
