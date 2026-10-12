# Operação: como saber que o número continua certo

Um resultado conferido uma vez não continua conferido para sempre. A tabela pública de
origem é republicada inteira sem aviso (em 12/10/2026 voltou com 30.028 linhas a menos do
que tinha nove dias antes) e as tabelas do modo gratuito do BigQuery expiram em 60 dias.

## O comando

```bash
python -m compras executar
```

Em ordem:

1. recria as 18 tabelas a partir de `sql/`;
2. roda os testes de qualidade de `sql/tests/`;
3. calcula os valores que o painel mostra e conta as linhas de cada tabela;
4. compara com a **referência** versionada: `powerbi/esperado.json` (valores do painel) e
   `sql/linhas.json` (linhas por tabela);
5. grava `relatorios/ultima.md` e `relatorios/ultima.json`.

Termina com erro se um passo quebrar, se um teste falhar ou se houver desvio.

## Como a comparação decide

- **Contagens** (linhas, fornecedores, órgãos) precisam ser idênticas.
- **Somas em reais** podem diferir em até uma parte em um trilhão (cerca de R$ 0,02 no
  total de R$ 15,8 bilhões). Duas execuções seguidas sobre os mesmos dados diferiram em
  cerca de uma parte em 10^15, na última casa que o número guarda; a tolerância fica mil
  vezes acima desse ruído. A causa provável é a ordem em que o BigQuery soma os valores
  (não verificado).
- Valor que sumiu ou apareceu também é desvio.

## Quando a execução falha

1. Abra o relatório. A seção "Mudou desde a referência" nomeia cada valor, com o antes, o
   depois e a variação.
2. Descubra a causa: a origem mudou (`recorte_igual_a_origem` falha junto), uma regra de
   limpeza mudou, ou o SQL mudou.
3. Se a mudança é legítima, aceite-a de forma explícita:

   ```bash
   python -m compras executar --aceitar
   git diff powerbi/esperado.json sql/linhas.json
   ```

   e abra um pull request. O número novo só passa a valer depois de revisado: a `main` não
   aceita envio direto.
4. Se não é legítima, corrija a causa. A referência não muda.

## Conferido em 12/10/2026

- Duas execuções seguidas: zero desvios em 41 valores comparados.
- Referência adulterada de propósito (uma linha a menos na fato e gasto total 1% menor): a
  execução terminou com erro e o relatório mostrou

  ```
  | total / Gasto Total | 15.647.279.788,4625 | 15.805.333.119,6591 | +1,0101% |
  | linhas / fato_item_compra | 334.900 | 334.901 | +0,0003% |
  ```

## Execução agendada

O workflow **Dados** roda o mesmo comando toda segunda-feira, às 09:00 UTC, e também por
disparo manual na aba Actions. O relatório aparece como resumo na página da execução e fica
anexado como arquivo. Execução vermelha quer dizer: um teste falhou ou um número mudou;
siga os passos de "Quando a execução falha".

