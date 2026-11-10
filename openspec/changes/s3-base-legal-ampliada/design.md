# Design

## Context

A coleta filtra artigos pelo campo `artigos` de `dados/fontes/fontes.yaml` (`app/rag/coleta.py:130`). Hoje o Código Penal lista quatro artigos, e `dados/fontes/dispositivos/` guarda só esses quatro. As expressões regulares em `app/rag/planalto.py:25` e `app/rag/resposta.py:45` capturam só dígitos seguidos, então "1.584" vira artigo 1. A verificação de citação (`verificar_citacoes`) aceita apenas normas de `LEIS_JURIDICAS` e trata qualquer outra "Lei N" mencionada como norma fora da base, recusando a resposta. O limite de similaridade é 0,81, com margem pequena (0,805 contra 0,818).

## Goals / Non-Goals

**Goals:**
- Ter na base, com texto integral e data, todos os artigos que as perguntas oficiais podem exigir.
- Citar corretamente artigos com separador de milhar.

**Non-Goals:**
- Ingerir o Código Civil ou o CPC inteiros.
- Mudar o modelo de embeddings ou o valor de `K`.
- Afrouxar a verificação de citação.

## Decisions

### Filtrar por artigos também nas novas normas
Código Civil e CPC entram em `fontes.yaml` no eixo `juridico`, com `artigos` restrito aos artigos decididos. Alternativa descartada: ingerir as duas normas inteiras, porque milhares de artigos fora do tema aumentariam o ruído da busca e o custo de memória.

### O artigo é guardado como a lei escreve
O campo `artigo` guarda "1.584", e a expressão aceita um grupo opcional de três dígitos depois do ponto. Assim, o rótulo exibido sai correto sem regra nova. Na comparação da citação, o ponto é ignorado, para aceitar também "art. 1584" escrito pelo LLM. O identificador interno do dispositivo usa o número sem ponto, porque o ponto já separa partes do identificador. Alternativa descartada: guardar "1584" e formatar na exibição, que exigiria tratar a formatação em cada lugar que mostra o artigo.

### Novas normas na verificação de citação
`LEIS_JURIDICAS` e `APELIDOS` passam a incluir Código Civil e Código de Processo Civil, inclusive "CPC" e os números das leis. A menção a "Lei 14.713/2023" é tratada como apelido das duas normas, porque ela alterou os dois artigos e o LLM pode citá-la junto. Sem isso, uma resposta correta seria recusada como norma fora da base. Alternativa descartada: incluir a Lei 14.713/2023 como norma própria, que duplicaria o mesmo texto já consolidado nos códigos.

### Recalibração só com perguntas de desenvolvimento
O limite é recalibrado depois da ampliação, com as 15 perguntas de desenvolvimento do tema e as 10 fora do tema, separadas do conjunto oficial. Usar as perguntas oficiais contaminaria a medição. Alternativa descartada: manter 0,81 sem recalibrar, porque a base nova muda a distribuição das similaridades.

## Risks / Trade-offs

- **O HTML do Planalto para Código Civil e CPC pode ter estrutura diferente** → A coleta aceita HTML já baixado (`--arquivo`), e o relatório de alterações é revisado antes da ingestão.
- **Mais trechos penais podem deslocar artigos da Lei Maria da Penha do top 5** → Rodar de novo o teste rápido, cuja meta continua em 9 de 10.
- **A ampliação pode juntar as faixas de similaridade do tema e de fora do tema** → A segunda camada (recusa sem citação) continua valendo, e o resultado da recalibração é registrado com os valores medidos.
- **Regex mais ampla pode ler números que não são artigos** → O grupo opcional exige exatamente três dígitos depois do ponto, e os testes cobrem artigos curtos e "Art. 147 - Ameaçar".

## Open Questions

- Os arts. 146 e 216-B do Código Penal, opcionais, entram só se a equipe quiser usá-los em perguntas antes do congelamento. Incluí-los é apenas acrescentar à lista em `fontes.yaml`.
