# Proposal

## Why

O entregável da S3 são respostas baseadas em evidências, e o critério de pronto da semana depende só do relatório comparativo entre o LLM com e sem RAG. O método da Semana 1 (50 perguntas e revisão em dupla) foi substituído pelas decisões de 09/11, então a spec precisa refletir o método que será usado de fato.

Métricas do ROADMAP afetadas: precisão jurídica (≥ 90%) e fidelidade às fontes (100% citadas, ≤ 5% sem suporte).

## What Changes

- Controle do raciocínio do modelo por variável de ambiente, necessário para usar o `deepseek-flash` sem raciocínio.
- Conjunto oficial de 30 perguntas dentro do tema, com gabarito e fonte, e 10 extras fora do tema, relatadas à parte. As perguntas de desenvolvimento ficam separadas.
- Perguntas e gabaritos escritos e conferidos pela equipe. Nenhum Claude escreve perguntas ou gabaritos.
- Rodada das duas versões no mesmo dia, com as mesmas instruções, exceto a regra de usar apenas os trechos.
- **BREAKING (método):** a revisão em dupla de 20% sai. A correção passa a ser feita por um único LLM externo, sem revisão humana das notas, e o relatório declara isso.
- Controles da correção: códigos neutros, ordem sorteada, respostas erradas de propósito e conferência automática do retorno.
- Relatório comparativo com o resultado real.
- **Plataforma:** a publicação contínua passa a valer a partir da S5.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `avaliacao`: substitui a revisão em dupla pela correção só por LLM e define o conjunto, as condições da rodada e os controles da correção.
- `plataforma`: acrescenta o controle do raciocínio por variável de ambiente e move a exigência de publicação para a S5.

## Impact

- **Código:** `app/config.py`, `app/llm.py`, `app/rag/resposta.py` (só a separação das instruções), novos scripts em `scripts/`.
- **Configuração:** `.env.example` e `README.md`. O `.env` local não é lido nem versionado, e cada máquina que chamar o DeepSeek precisa da própria chave.
- **Dados:** nova pasta `avaliacao/`, com conjuntos, rubricas e rodadas.
- **Depende de:** `s3-base-legal-ampliada`, porque as perguntas e a correção de fidelidade usam os artigos ampliados.
- **Privacidade (LGPD):** segue a opção (c), registrada em `s2-plataforma-base/design.md`. Só casos fictícios vão ao DeepSeek e ao LLM externo, e o risco é declarado no relatório.
- **Segurança da usuária:** cada pergunta passa por `app.risco.avaliar` antes de congelar. Quando dispara, a pergunta é reescrita de forma impessoal, sem afrouxar as regras de risco.
- **Fora desta mudança:** revisão humana das notas, ampliação da base legal, correção da lacuna do `/juridico` quando o alerta dispara (S4), deploy (S5).
