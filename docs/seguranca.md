# Segurança do repositório

## Acesso do GitHub ao BigQuery

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

Não conferido: o script ainda não foi executado. Falta provar (1) que o modo gratuito do
BigQuery aceita a federação, (2) que uma execução disparada de outra branch não recebe
credencial e (3) que a conta de serviço não escreve fora do conjunto `compras`.

