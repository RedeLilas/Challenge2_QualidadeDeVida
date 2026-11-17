# Tasks

Primeira mudança a cortar se a S4 apertar (vai para a S6). Depende da tarefa 1.1 de `s4-orquestrador-agentes` (parametrizar `responder()`, terça cedo).

## 1. Perguntas de desenvolvimento (terça, 17/11)

- [ ] 1.1 Escrever com o Claude `avaliacao/conjuntos/s4/desenvolvimento_beneficios.yaml`: cerca de 20 perguntas leigas cobrindo os seis programas (com apelidos, erros de digitação e parte sem o nome oficial), gabarito e norma (artigo) tirados de `dados/leis/`, cerca de 8 extras quase do tema e a pergunta "como funciona o aluguel da Maria da Penha?" marcada para o eixo jurídico; verificação: o arquivo carrega, cada pergunta passa pela regra de risco, e `avaliacao/conjuntos/desenvolvimento.yaml` não mudou (`git diff`)
- [ ] 1.2 Validar o conjunto em `scripts/validar_conjuntos.py` (norma e artigo, autor, revisor diferente do autor, perguntas sem o nome oficial, extras, a pergunta do jurídico) e, para um futuro conjunto de medição de benefícios, a ausência de perguntas repetidas do desenvolvimento; verificação: testes em `tests/test_validar_conjuntos.py` cobrem pergunta sem norma, revisor igual ao autor e pergunta repetida

## 2. Verificação de citação (terça, 17/11)

- [x] 2.1 Criar as configurações `JURIDICO` e `BENEFICIOS` da verificação, com o `/juridico` passando `JURIDICO` com os valores de hoje; verificação: `tests/test_juridico.py` passa sem alteração
- [x] 2.2 Acrescentar os apelidos das 11 normas de benefícios, com e sem o ano e com e sem "Distrital"; verificação: testes com trechos fictícios aceitam "(Lei 8.742/1993, art. 20)", "(LOAS, art. 20)", "(Lei 6.623, art. 1º)" e "(Lei Distrital 6.623, art. 1º)" quando o artigo foi recuperado, e recusam "(Decreto 42.376, art. 3º)" e "(Lei Distrital 6.623, art. 1º)" quando o único artigo com esse número é de outra norma
- [x] 2.3 Recusar, na configuração `BENEFICIOS`, artigo sem norma reconhecida quando os trechos vêm de mais de uma norma; verificação: testes cobrem a recusa com várias normas, a aceitação com uma norma só e o mesmo caso no jurídico, que continua com o resultado de antes

## 3. Resposta de benefícios (terça, 17/11, e quinta, 19/11)

- [x] 3.1 Escrever `INSTRUCOES_BENEFICIOS`, a recusa de benefícios (CRAS e Ligue 180) e o aviso fixo com a data da coleta mais antiga das normas citadas (terça); verificação: testes com LLM falso conferem a instrução enviada, o aviso com a data e a recusa, e um teste confere que nenhum texto fixo usa "direito garantido"
- [ ] 3.2 Criar o teste de recuperação por benefício nos eixos `beneficios` e `df`, com a norma certa no top 5 (terça); verificação: o teste passa para os seis programas ou registra no design o benefício que falha e o motivo
- [ ] 3.3 Calibrar `LIMITE_BENEFICIOS` só com o conjunto de desenvolvimento de benefícios, conferir a pergunta do aluguel da Maria da Penha contra o 0,81 do jurídico e registrar o valor, as faixas e a data no design (quinta); verificação: um teste com o índice real confere que as extras quase do tema são recusadas pelo limite ou pela citação, e o design traz os números
- [ ] 3.4 Registrar a explicação de benefícios no ponto de troca do `/orquestrar` (quinta); verificação: testes com índice e LLM falsos conferem que a explicação busca só nos eixos `beneficios` e `df`, com o limite próprio, e que, sem o registro, ela volta ao jurídico

## 4. Fechamento (quinta, 19/11)

- [ ] 4.1 Rodar a suíte de risco/190 e a suíte completa e testar no navegador três perguntas de explicação (uma sem o nome oficial) e uma de FGTS; verificação: `uv run pytest` passa sem falso negativo, e o teste manual fica registrado no design
- [ ] 4.2 Declarar no relatório da S4 que o RAG de benefícios foi testado e não medido, sem corretor externo, e atualizar o status no `ROADMAP.md`; verificação: o relatório e a tabela da S4 trazem a declaração e o status

## Workflow follow-up

- Arquivar a mudança depois de `openspec validate s4-rag-beneficios` passar e de atualizar o `ROADMAP.md`. Se for cortada, mover a linha do ROADMAP para a S6.
