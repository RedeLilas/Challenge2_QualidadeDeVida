# Proposal

## Why

As definições da Semana 1 (`docs/Challenge 2 - Definições do Projeto Semana 1.md`) descrevem requisitos, métricas e riscos em texto livre. Para guiar o desenvolvimento das semanas 2 a 7 com o OpenSpec, esses requisitos precisam virar specs verificáveis (requisitos com cenários WHEN/THEN) que a equipe e o assistente de IA consultem em toda mudança.

Esta mudança também incorpora três decisões tomadas depois da Semana 1:

- **Escopo DF:** rede de serviços apenas do Distrito Federal, por Região Administrativa ou CEP; legislação federal + normas distritais.
- **Sem entrevistas:** validação só com casos fictícios, gabarito da equipe com fonte, LLM juiz e revisão em dupla; usabilidade com colegas.
- **Stack e deploy:** Python + PWA, LLM local nos testes e DeepSeek em produção, deploy desde a S2.

## What Changes

- Cria 9 capacidades com os requisitos da Semana 1 (RF01–RF09, RNF01–RNF06, métricas da seção 8), ajustados ao DF e à ausência de entrevistas.
- Amplia o RF06 (rede de saúde) para `rede-atendimento`: CNES do DF + lista curada da rede de proteção do DF (Casa da Mulher Brasileira, CEAMs, DEAMs, Defensoria).
- Troca "município" por "Região Administrativa ou CEP" no perfil (RF01).
- Remove a nota de 1 a 5 de profissionais da rede; o SUS passa a ser aplicado com colegas.
- Adiciona requisitos explícitos para o modo "estou ajudando outra pessoa" (persona Camila).
- Adiciona as capacidades `plataforma` (provedor de LLM e deploy) e `avaliacao` (medição das métricas).

## Capabilities

### New Capabilities
- `triagem-risco`: alerta de risco imediato (190) por regra e triagem de urgência baseada no Fonar.
- `orientacao-juridica`: respostas sobre a Lei Maria da Penha com citação de artigo, via RAG, e recusa quando não há fundamentação.
- `beneficios`: regras auditáveis de elegibilidade para benefícios federais e distritais, com o que falta e onde pedir no DF.
- `rede-atendimento`: serviços de proteção e de saúde do DF mais próximos por RA ou CEP, com data do dado.
- `privacidade-seguranca`: perfil mínimo local, saída rápida, ausência de histórico, disfarce e proteção de dados (LGPD).
- `conversa`: chat com perguntas sugeridas, orquestração entre agentes, modo de ajuda a terceiros e entrada multimodal.
- `interface-pwa`: linguagem simples, acessibilidade, desempenho e funcionamento em celular básico e conexão lenta.
- `plataforma`: provedor de LLM configurável, configuração segura e implantação contínua.
- `avaliacao`: conjunto de casos fictícios, LLM juiz, comparação LLM x RAG e metas de qualidade.

### Modified Capabilities

Nenhuma (não há specs anteriores).

## Impact

- Cria `openspec/specs/` com 9 specs ao ser arquivada.
- Serve de referência para todas as mudanças das semanas 2 a 7 (ver `ROADMAP.md`).
- Nenhum código é afetado.
- Fora desta mudança: decisões de implementação (ficam nos `design.md` de cada mudança) e as duas decisões pendentes da S2 (plataforma de deploy e tratamento LGPD do DeepSeek).
