# Relatório S4: sistema multiagentes

Avaliação parcial registrada em 19/11/2026; a S4 continua em andamento. Os conjuntos de elegibilidade, triagem e roteamento foram escritos por Léo e conferidos por outra pessoa da equipe, conforme os revisores registrados nos próprios arquivos. Não houve corretor externo nesta avaliação.

## Resultados

| Medida | Resultado | Interpretação |
|---|---:|---|
| Elegibilidade | Não confirmada no estado final do gabarito | A medição inicial não é válida após a correção do caso e-013; é preciso reexecutá-la com o gabarito final. |
| Sensibilidade para risco alto | 38/38 (100%) | Meta de 100% atingida; cinco casos de triagem de alto risco e 33 frases de risco imediato. |
| Roteamento | 29/30 (96,7%) | Evidência sem meta. Regra determinística: 19/19; modelo nos demais casos: 10/11. |

### Roteamento

A rodada foi executada em 19/11/2026 contra a API de produção, com o alias `deepseek-flash` e raciocínio desativado. O alias correspondia à versão DeepSeek-V4.1-Flash-1017, conforme o changelog do fornecedor. Os 19 casos resolvidos pela regra acertaram; entre os 11 enviados ao modelo, houve dez acertos e uma divergência: **r-027**, esperado `juridico`, retornou `beneficios`. O resultado detalhado, incluindo os IDs dos casos, está em `avaliacao/rodadas/s4/roteamento.yaml`.

Os casos são fictícios; nenhum perfil real ou dado pessoal foi enviado. A medição registra apenas resultados e metadados da rodada.

### Elegibilidade e risco

A elegibilidade compara cada situação esperada nos 20 perfis com os quatro benefícios avaliados, totalizando 80 pares. A medição inicial de 80/80 foi feita antes da correção do gabarito de `e-013` e não pode ser usada para afirmar a meta atingida; o resultado precisa ser reexecutado contra o conjunto final antes de fechar essa métrica. A sensibilidade para risco alto combina cinco casos de triagem cujo resultado esperado é alto com 33 frases de risco imediato; todos dispararam o resultado esperado. Não houve falso negativo nem divergência nos controles.

## Escopo e limitações

O RAG de explicação de benefícios continua no escopo da S4. Sua validação final e integração ainda estão pendentes; por isso, este relatório não afirma que foi testado ou medido. A S4 permanece aberta até a conclusão das tarefas restantes.

O roteamento é uma evidência de 30 mensagens fictícias e não possui meta de aprovação. O resultado representa uma única rodada com o modelo e a configuração identificados acima; não mede latência nem estabilidade entre rodadas. Risco verifica regras determinísticas locais contra gabaritos revisados, sem corretor LLM externo. A acurácia de elegibilidade segue pendente de nova execução após a revisão do gabarito `e-013`. Essas pendências mantêm a avaliação parcial; não representam atraso nem decisão de transferência para outra sprint.
