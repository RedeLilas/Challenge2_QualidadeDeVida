# Proposal

## Why

O entregável do curso na S2 é o primeiro mecanismo de RAG. A pergunta jurídica ("o que ele faz comigo é crime?") é o centro das duas personas, e responder com o artigo da lei citado é o que torna a resposta verificável e reduz alucinação. Esta mudança cria o RAG sobre a Lei Maria da Penha, que a S3 vai comparar com o LLM sem RAG.

Métricas do ROADMAP afetadas: precisão jurídica (≥ 90%) e fidelidade às fontes (100% citadas, ≤ 5% sem suporte), medidas na S3.

## What Changes

- Ingestão da Lei 11.340/2006 a partir do site do Planalto, dividida por artigo, com URL e data de acesso em cada trecho.
- Índice de embeddings local (modelo multilíngue) em memória.
- Rota de pergunta jurídica: recupera os trechos, gera a resposta com o LLM e devolve a resposta com as citações.
- Verificação de citação: a resposta só é exibida se os artigos citados estiverem entre os recuperados.
- Recusa quando a similaridade fica abaixo de um limite, indicando o Ligue 180 e a Defensoria Pública do DF.
- Teste rápido com 10 perguntas no estilo das personas.

Requisitos implementados (specs da base): `orientacao-juridica` (Resposta fundamentada com citação; Identificação das formas de violência; Recusa sem fundamentação; Base legal versionada).

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

Nenhuma. A mudança implementa requisitos já definidos em `s1-definicoes-base`.

## Impact

- Depende de `s2-plataforma-base` (cliente de LLM) e passa pela verificação de `s2-alerta-risco-190`.
- Adiciona dependência de um modelo de embeddings local (memória extra no deploy).
- **Privacidade (LGPD):** a pergunta é enviada ao LLM; em produção, segue a decisão registrada em `s2-plataforma-base`.
- **Segurança da usuária:** respostas sem fundamentação são recusadas em vez de inventadas.
- **Fora desta mudança:** outras normas (Lei 14.149/2021, leis de benefícios), busca híbrida e avaliação completa (S3).
