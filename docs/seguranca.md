# Segurança do repositório

O que está ligado, o que cada coisa impede e como foi conferido. As configurações foram
aplicadas por comando (`gh api`), para poderem ser repetidas e auditadas.

## O que está ligado

| Configuração | O que impede |
|---|---|
| `main` protegida: só por pull request, com a verificação "lint, tipos e testes" verde | código que não passou pelos testes chegar à versão publicada |
| Regra vale também para o dono do repositório | o atalho "só desta vez" |
| Sem envio forçado e sem apagar a `main` | reescrever ou perder o histórico |
| Varredura de segredos, com bloqueio no envio | uma senha ou chave ficar gravada no histórico, de onde apagar o arquivo não a remove |
| Alertas e correções do Dependabot | continuar usando uma biblioteca com falha conhecida |
| Ações do workflow fixadas pelo identificador do commit | uma etiqueta como `v4` passar a apontar para outro código sem aviso |
| `permissions: contents: read` no workflow | um passo comprometido escrever no repositório |

## O que este repositório não guarda

Nenhuma credencial. O acesso ao BigQuery usa o login de quem roda (`gcloud auth login`); o
arquivo `.env` está no `.gitignore` e não é usado pelo código.

## Comandos aplicados (12/10/2026)

```bash
R=diaquinodev/inteligencia-de-compra

# varredura de segredos e bloqueio no envio
gh api -X PATCH repos/$R --input - <<'EOF'
{"security_and_analysis":{"secret_scanning":{"status":"enabled"},
 "secret_scanning_push_protection":{"status":"enabled"}}}
EOF

# alertas e correções automáticas de dependências
gh api -X PUT repos/$R/vulnerability-alerts
gh api -X PUT repos/$R/automated-security-fixes

# proteção da main
gh api -X PUT repos/$R/branches/main/protection --input - <<'EOF'
{"required_status_checks":{"strict":false,"contexts":["lint, tipos e testes"]},
 "enforce_admins":true,
 "required_pull_request_reviews":{"required_approving_review_count":0},
 "restrictions":null,"allow_force_pushes":false,"allow_deletions":false}
EOF
```

O número de aprovações exigidas é zero porque o repositório tem um único mantenedor, e o
GitHub não deixa ninguém aprovar o próprio pull request. O controle que sobra é o que
importa aqui: nada entra sem os testes verdes.

## Conferência

Envio direto para a `main`, feito de propósito em 12/10/2026 com um commit vazio:

```
remote: - Changes must be made through a pull request.
remote: - Required status check "lint, tipos e testes" is expected.
 ! [remote rejected] HEAD -> main (protected branch hook declined)
```

Estado lido de volta com `gh api repos/$R --jq .security_and_analysis`: `secret_scanning`,
`secret_scanning_push_protection` e `dependabot_security_updates` como `enabled`.

Não conferido: o bloqueio de segredo no envio não foi testado com um segredo de verdade
nem com um falso; está ligado, mas a prova de que barra um envio ainda não existe.
