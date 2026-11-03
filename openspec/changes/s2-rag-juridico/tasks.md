# Tasks

## 1. Ingestão e índice (quinta, 05/11)

- [ ] 1.1 Escrever o script de ingestão: baixa a Lei 11.340/2006 do Planalto, remove trechos revogados (`<strike>`) e divide por artigo; verificação: teste que confere o número de artigos e a ausência de texto revogado
- [ ] 1.2 Gerar `dados/leis/lei_11340.jsonl` com metadados (lei, artigo, inciso, url, data de acesso); verificação: todos os registros têm url e data
- [ ] 1.3 Implementar o índice de embeddings com `multilingual-e5-small`; verificação: teste que busca "violência patrimonial" e recupera o art. 7º
- [ ] 1.4 Escrever `tests/perguntas_juridicas.yaml` com 10 perguntas no estilo das personas e os artigos esperados; verificação: o artigo esperado aparece no top 5 em pelo menos 9 das 10

## 2. Resposta com citação (sexta, 06/11)

- [ ] 2.1 Criar a rota de pergunta jurídica (recuperação + prompt + LLM) devolvendo `resposta` e `citacoes`; verificação: teste com LLM simulado
- [ ] 2.2 Implementar a verificação de citação; verificação: teste em que o LLM simulado cita um artigo não recuperado e a resposta é descartada
- [ ] 2.3 Implementar e calibrar o limite de recusa; verificação: 3 perguntas fora do tema são recusadas com indicação do Ligue 180 e da Defensoria do DF
- [ ] 2.4 Exibir resposta e citações na PWA; verificação: pergunta da persona Camila respondida na URL publicada com art. 7º citado
- [ ] 2.5 Atualizar o status no `ROADMAP.md` e arquivar a mudança
