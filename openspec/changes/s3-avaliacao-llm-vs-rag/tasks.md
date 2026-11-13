# Tasks

## 1. Modelo de produção (terça, 10/11)

- [x] 1.1 Adicionar `LLM_THINKING` opcional em `app/config.py` e `extra_body` em `app/llm.py`; verificação: testes com cliente simulado em `tests/test_config.py` e `tests/test_llm.py` cobrem a variável definida, ausente e inválida
- [x] 1.2 Atualizar `.env.example` e `README.md` para `deepseek-flash`, sem raciocínio e sem chave; verificação: `grep deepseek-chat .env.example README.md` não encontra nada e não há chave versionada

## 2. Conjuntos de perguntas (terça, 10/11, a quinta, 12/11)

- [x] 2.1 Definir o formato de `avaliacao/conjuntos/` e criar o validador do conjunto; verificação: testes com fixtures fictícias falham para campo faltando, distribuição errada, falta de segunda pessoa e pergunta que dispara o alerta
- [ ] 2.2 Equipe completa as perguntas de desenvolvimento (15 do tema e 10 fora do tema), separadas do conjunto oficial, sem usar Claude; verificação: o validador do conjunto de desenvolvimento passa
- [x] 2.3 Equipe escreve as 19 perguntas que usam só a Lei 11.340/2006, com gabarito, pontos obrigatórios, normas aceitas e fonte, sem usar Claude; verificação: o validador aponta só as perguntas ainda não escritas
- [x] 2.4 Equipe escreve as 11 perguntas restantes e as 10 extras fora do tema, sem usar Claude; verificação: o conjunto tem a distribuição decidida
- [x] 2.5 Segunda pessoa confere cada gabarito no texto da lei e registra a conferência; verificação: o validador do conjunto oficial passa por inteiro

## 3. Scripts da rodada e da correção (terça, 10/11, a quinta, 12/11)

- [x] 3.1 Separar as instruções das duas versões, sem mudar a resposta da versão com RAG; verificação: teste confere que só as frases sobre trechos diferem
- [x] 3.2 Criar o script da rodada, que gera as duas versões e registra modelo, data, versão do changelog e instruções; verificação: teste com LLM simulado grava o registro completo e recusa rodar a oficial com hash divergente
- [x] 3.3 Criar o script dos arquivos enviados, com códigos neutros, sorteio com semente, respostas erradas de propósito e mapa separado; verificação: teste confere que os arquivos não trazem indicação de versão e que uma resposta errada fica perto do final
- [x] 3.4 Criar o script de conferência do retorno e cálculo de precisão, fidelidade, recusa e citação; verificação: testes cobrem linha faltando, trecho inexistente, resposta errada aprovada e recusa contada como erro

## 4. Teste com as perguntas de desenvolvimento (quinta, 12/11)

- [ ] 4.1 Escrever as rubricas de precisão e de fidelidade e registrar a escolha do LLM externo; verificação: as rubricas estão em `avaliacao/rubricas/` e o modelo escolhido está registrado na rodada
- [ ] 4.2 Rodar as duas versões com as perguntas de desenvolvimento e o DeepSeek; verificação: o registro da rodada existe e o tamanho das respostas e as recusas foram revisados
- [ ] 4.3 Enviar ao LLM externo e conferir o retorno; verificação: o script aceita o retorno, e nenhuma resposta errada de propósito foi aprovada

## 5. Rodada oficial e relatório (quinta, 12/11, e sexta, 13/11)

- [ ] 5.1 Congelar o conjunto oficial; verificação: o hash está registrado e o validador passa
- [ ] 5.2 Rodar as duas versões no mesmo dia com o conjunto oficial; verificação: a rodada tem as 30 respostas de cada versão e as 10 extras
- [ ] 5.3 Fazer os quatro envios e guardar tudo o que foi enviado e recebido; verificação: o script aceita os quatro retornos
- [ ] 5.4 Equipe lê as 10 extras nas duas versões e registra as observações; verificação: a seção das extras está no relatório
- [ ] 5.5 Escrever o relatório comparativo em `docs/`, lado a lado, com o risco da opção (c), a declaração "avaliação feita por LLM, sem verificação humana das notas" e o resultado real; verificação: precisão e fidelidade das duas versões aparecem na tabela e `uv run pytest` passa, incluindo a suíte de risco/190

## Workflow follow-up

- Atualizar o status no `ROADMAP.md` e arquivar a mudança, depois de `openspec validate s3-avaliacao-llm-vs-rag` passar.
- Depois de arquivar, ajustar o `## Purpose` de `openspec/specs/avaliacao/spec.md`, que ainda cita a revisão humana em amostra.
