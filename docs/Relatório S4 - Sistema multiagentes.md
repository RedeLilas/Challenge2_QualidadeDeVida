# Relatório S4: sistema multiagentes

Avaliação da S4, com medições em 17 e 19/11/2026. A S4 permanece em andamento enquanto a validação final de integração não for concluída. Os metadados dos conjuntos registram Léo como autor dos casos de elegibilidade, triagem e roteamento; as ferramentas usadas para redigir foram Claude (elegibilidade) e Codex (triagem e roteamento). Os revisores estão identificados nos metadados de cada conjunto. Não houve corretor externo na S4.

## Resultados

| Medida | Resultado | Critério |
|---|---:|---|
| Elegibilidade, antes da correção #110 | 79/80 (98,75%) | Meta ≥ 90%, atingida. Divergência única em e-013 / Aluguel Social. |
| Elegibilidade, após a correção #110 | 80/80 (100%) | Meta ≥ 90%, atingida; regra usa renda familiar total quando falta o número de pessoas. |
| Sensibilidade para risco alto | 38/38 (100%) | Meta 100%, atingida: 5 casos de triagem de alto risco e 33 frases de risco imediato. |
| Roteamento, 17/11 | 28/30 (93,3%) | Evidência sem meta; erros r-007 e r-027. |
| Roteamento, 19/11, rodada 1 | 29/30 (96,7%) | Evidência sem meta; erro r-027. |
| Roteamento, 19/11, rodada 2 | 28/30 (93,3%) | Evidência sem meta; r-005 foi para a reserva jurídica e r-027 foi classificado como benefícios. |

### Elegibilidade

A rodada oficial antes da correção #110 comparou 20 perfis × 4 benefícios (80 pares): acertou 79/80 (98,75%). A única divergência foi e-013, Aluguel Social: com renda familiar de R$ 400 e número de pessoas desconhecido, o gabarito derivado da Portaria SMDF 49/2026, art. 2º, I, indicava `provavel`, mas a regra retornava `faltam_informacoes`. A issue #110 ajustou a regra para usar o limite de renda familiar total quando o número de pessoas não é conhecido. A nova execução com a regra corrigida acertou 80/80 (100%). Os dois resultados são mantidos separadamente: o primeiro mede a regra antes da correção e o segundo demonstra o resultado após a correção.

### Risco alto

O script `scripts/medir_s4.py` avaliou os 14 casos de triagem e as 33 frases positivas da suíte de risco imediato. Os cinco casos cujo gabarito era alto e as 33 frases acionaram o resultado esperado: 38/38 positivos, sem falso negativo; não houve falso positivo nos controles nem divergência de nível na triagem.

### Roteamento e variação entre rodadas

As três rodadas usaram o modelo `deepseek-flash`, raciocínio desativado e temperatura 0. A versão documentada no changelog para as rodadas de 19/11 era DeepSeek-V4.1-Flash-1017. Os resultados completos, com metadados, hashes, por etapa e por caso, estão em `avaliacao/rodadas/s4/`:

- 17/11: 28/30; erros r-007 (esperado benefícios/direito, obtido jurídico) e r-027 (esperado jurídico, obtido benefícios).
- 19/11, rodada 1: 29/30; erro r-027.
- 19/11, rodada 2: 28/30; r-005 foi para a reserva jurídica após falha do modelo, e r-027 foi obtido como benefícios.

A diferença de r-007 entre rodadas e a falha que levou r-005 à reserva mostram variação na classificação por LLM. A taxa de roteamento é evidência sem meta e não deve ser interpretada como estabilidade garantida.

## RAG de benefícios

O RAG de explicação de benefícios permanece na S4, integrado ao `/orquestrar`. Foi testado, mas não medido com um conjunto oficial e corretor externo. Os testes de recuperação cobrem os seis programas; 22/22 perguntas de desenvolvimento recuperam a norma esperada no top 5 dos eixos `beneficios` e `df`. A calibração do limite próprio e a verificação de citação estão registradas no design de `s4-rag-beneficios`. Portanto, o relatório declara teste funcional, sem apresentar uma taxa de qualidade de respostas do RAG. A suíte completa e os cenários manuais finais da S4 continuam pendentes.

## Ajustes depois do teste manual (19/11)

O teste manual de fechamento encontrou dois problemas, corrigidos no mesmo dia, depois das medições acima:
- **Classificação do tipo de benefício:** perguntas como "o governo do df ajuda quando nasce um bebe?" eram classificadas pelo LLM como "tenho direito?", e o chat mostrava cartões de elegibilidade que não respondiam. Agora "direito" vale só para os 4 benefícios com regra ou quando a mensagem pergunta se a pessoa tem direito; nos demais casos, a pergunta vai à explicação (RAG de benefícios). As rodadas de roteamento mediram a classificação anterior.
- **Tamanho das respostas:** as respostas da conversa passaram a ter no máximo 5 frases curtas (jurídico na conversa e RAG de benefícios). O RAG de benefícios também deixou de citar artigos que só aparecem dentro de outros, o que recusava respostas corretas. O `/juridico` avaliado na S3 não mudou.

## Método e limitações

A elegibilidade e a sensibilidade para risco foram medidas contra gabaritos de casos fictícios em regras locais/QuickJS, sem LLM como corretor. A classificação de roteamento usou a API de produção em mensagens fictícias. Nenhum dado pessoal foi enviado. A re-derivação dos 80 pares de elegibilidade foi feita por Claude a partir das normas, sem consultar o gabarito nem executar a regra; como Claude já conhecia a regra, isso não equivale a uma conferência cega por uma pessoa. A revisão humana e as ferramentas de redação estão identificadas nos metadados e no design.
