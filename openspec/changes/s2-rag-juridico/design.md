# Design

## Context

A Lei 11.340/2006 tem poucas dezenas de artigos, então a base é pequena. O DeepSeek não oferece API de embeddings, por isso eles são gerados localmente, inclusive no deploy. As perguntas das usuárias usam linguagem leiga ("quebrou meu celular"), diferente do vocabulário da lei ("subtração, destruição parcial ou total de seus objetos"), então a busca precisa ser semântica.

## Goals / Non-Goals

**Goals:**
- Responder perguntas sobre a Lei Maria da Penha citando o artigo correto.
- Recusar quando a base não sustenta a resposta.

**Non-Goals:**
- Banco vetorial externo.
- Outras normas além da Lei 11.340/2006.
- Avaliação formal (fica em `s3-avaliacao-llm-vs-rag`).

## Decisions

### Ingestão e divisão por artigo
- Fonte: página do texto compilado da Lei 11.340/2006 no Planalto.
- O HTML do Planalto mostra trechos revogados riscados (elementos `<strike>`), que precisam ser **removidos** antes da divisão.
- Um trecho por artigo. Artigos longos (ex.: art. 22, medidas protetivas) podem ser divididos por inciso, mantendo a referência ao artigo em cada parte.
- Metadados: `lei`, `artigo`, `inciso` (se houver), `url`, `data_acesso`.
- Saída versionada em `dados/leis/lei_11340.jsonl`, para que mudanças no texto apareçam no diff.

### Embeddings e índice
- Modelo: `intfloat/multilingual-e5-small` (multilíngue, pequeno). Usa os prefixos `query:` e `passage:`.
- Índice em memória (matriz de vetores + similaridade de cosseno), gerado na inicialização ou carregado de um arquivo pré-calculado.
- Alternativa considerada: um banco vetorial (Chroma). Descartado por ser desnecessário para algumas dezenas de trechos.

### Geração com citação
- Recupera os 5 trechos mais similares.
- O prompt instrui a responder só com base nos trechos, em linguagem simples, citando no formato "(Lei 11.340/2006, art. N)".
- Após a geração, o código extrai os artigos citados e confere se estão entre os recuperados. Se não estiverem, a resposta é descartada e o sistema recusa.
- A rota devolve `resposta` e `citacoes` (lei, artigo, url, data de acesso).

### Recusa por baixa similaridade
Se a maior similaridade ficar abaixo de um limite, o sistema recusa sem chamar o LLM. O limite inicial é calibrado com as 10 perguntas do teste rápido e algumas perguntas fora do tema.

### Teste rápido
`tests/perguntas_juridicas.yaml`, com 10 perguntas no estilo das personas e os artigos esperados (ex.: "ele quebrou minhas coisas, isso é violência?" → art. 7º, IV). Meta: o artigo esperado aparece entre os 5 recuperados em pelo menos 9 das 10 perguntas.

## Risks / Trade-offs

- **Modelo de embeddings pesa na memória do deploy**: considerado na escolha da plataforma (`s2-plataforma-base`).
- **Limite de similaridade mal calibrado**: alto demais gera recusas desnecessárias; baixo demais deixa passar respostas fracas. Será recalibrado com as 50 perguntas da S3.
- **Mudanças no HTML do Planalto quebram a ingestão**: o texto processado fica versionado em `dados/leis/` e só é regenerado na revisão mensal.
