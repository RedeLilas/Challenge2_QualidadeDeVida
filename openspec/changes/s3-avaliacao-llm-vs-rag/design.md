# Design

## Context

O cliente em `app/llm.py` não envia `extra_body`, e `app/config.py` lê apenas quatro variáveis. As instruções da versão com RAG estão em `INSTRUCOES` (`app/rag/resposta.py`). Só 10 das 15 perguntas de desenvolvimento estão versionadas (`tests/perguntas_juridicas.yaml`), e as 10 fora do tema não estão no repositório. O LLM externo ainda não foi escolhido. Nenhuma rodada com o DeepSeek foi feita, e o envio de 30 respostas de uma vez não foi testado.

## Goals / Non-Goals

**Goals:**
- Tornar a rodada e a correção reproduzíveis e auditáveis.
- Impedir que o conjunto oficial mude sem registro depois do resultado.

**Non-Goals:**
- Automatizar o envio ao LLM externo. Os quatro envios são feitos manualmente, na interface dele.
- Medir latência (S6).

## Decisions

### Raciocínio controlado por variável opcional
`LLM_THINKING` é opcional. Com o valor `disabled`, o cliente envia `extra_body={"thinking": {"type": "disabled"}}`. Sem a variável, nada muda para o Ollama. Alternativa descartada: enviar sempre o parâmetro, porque ele é específico do DeepSeek e o modelo local não deve depender dele.

### Pasta `avaliacao/` versionada
- `avaliacao/conjuntos/`: `desenvolvimento.yaml` e `oficial.yaml`, escritos pela equipe.
- `avaliacao/rubricas/`: textos das correções de precisão e de fidelidade.
- `avaliacao/rodadas/<data>-<id>/`: respostas, arquivos enviados, retornos, modelo e data.

O mapa de versões fica em um arquivo separado da rodada, que nunca é enviado ao corretor. Só há casos fictícios, então tudo pode ser versionado.

### Congelamento por hash
O congelamento grava o SHA-256 de `oficial.yaml`. A rodada oficial compara o hash e recusa executar se ele divergir. Alternativa descartada: congelar apenas por combinação da equipe, que não deixa evidência.

### Validador do conjunto
Um script confere a distribuição por tema, os campos obrigatórios, o registro de segunda pessoa e `app.risco.avaliar` em cada pergunta. O validador também roda em `tests/`, com fixtures fictícias próprias, sem usar o conjunto oficial.

### Instruções da versão sem RAG
A versão sem RAG remove a regra "Responda usando apenas os trechos". As outras duas frases que mencionam trechos são adaptadas só no necessário para fazer sentido sem eles: mantém-se o formato de citação e a orientação de dizer que não sabe. As duas listas de instruções ficam na rodada, para auditoria. Alternativa descartada: reescrever as instruções da versão sem RAG, que deixaria de ser uma comparação justa.

### Arquivos enviados ao corretor
Cada pergunta tem uma versão sorteada para o arquivo A e a outra para o arquivo B. O sorteio usa uma semente registrada na rodada. Cada arquivo tem 30 respostas e 3 respostas erradas de propósito, escritas pela equipe a partir de perguntas de desenvolvimento, para não alterar as 30 do conjunto oficial. O texto integral dos artigos citados vem do arquivo mais recente de `dados/fontes/dispositivos/`.

### Detecção por código
Recusa é a resposta igual ao texto de recusa do sistema. Presença de citação usa a mesma extração da verificação de citação. Essas duas medidas não vão ao corretor.

## Risks / Trade-offs

- **Sem revisão humana, um erro sistemático do corretor passa despercebido** → Respostas erradas de propósito, trechos comprobatórios e a declaração no relatório.
- **O curso pode não aceitar 30 perguntas e correção só por LLM** → Confirmar antes do congelamento. A pendência continua aberta, e `docs/` ainda promete o método da Semana 1.
- **O corretor pode truncar 33 linhas em uma conversa** → O teste com as perguntas de desenvolvimento valida o formato, e o script aponta linhas faltantes.
- **O nome `deepseek-flash` não fixa uma versão** → Rodar as duas versões no mesmo dia e registrar nome, data e versão do changelog.
- **As perguntas podem ficar prontas só no meio da quinta** → A rodada pode passar para a manhã de sexta, e o relatório continua sendo a prioridade.

## Open Questions

- Qual LLM externo será usado. A escolha precisa sair antes do teste de quinta e é registrada na tarefa correspondente. Se ele não aceitar o formato, muda-se o modelo, sem mudar as specs.
