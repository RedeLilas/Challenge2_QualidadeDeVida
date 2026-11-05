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
- Modelo: `intfloat/multilingual-e5-base` (multilíngue). Usa os prefixos `query:` e `passage:`.
- Alternativa descartada: `intfloat/multilingual-e5-small`, a escolha inicial. No teste rápido da tarefa 1.4 (03/11), com os mesmos 109 trechos, o `e5-small` trouxe o artigo esperado no top 5 em 7 de 10 perguntas, abaixo da meta de 9. O `e5-base` acertou 10 de 10. O `e5-small` errou perguntas em linguagem leiga: "me xinga e me chama de burra" (art. 7º), "namorado não mora comigo" (art. 5º) e "proibir ele de chegar perto" (art. 22). Custo da troca: cerca de 1,1 GB em disco e memória, contra cerca de 470 MB, a considerar na plataforma de deploy (`s2-plataforma-base`).
- Divisão testada junto: limites menores por trecho (600 caracteres ou um trecho por dispositivo) não melhoraram o `e5-small` e pioraram o `e5-base`. Mantido o limite de 1500 caracteres, com a citação e o capítulo no texto do embedding.
- Índice em memória (matriz de vetores + similaridade de cosseno), gerado na inicialização ou carregado de um arquivo pré-calculado.
- Alternativa considerada: um banco vetorial (Chroma). Descartado por ser desnecessário para algumas dezenas de trechos.

### Geração com citação
- Recupera os 5 trechos mais similares.
- O prompt instrui a responder só com base nos trechos, em linguagem simples, citando no formato "(Lei 11.340/2006, art. N)".
- Após a geração, o código extrai os artigos citados e confere se estão entre os recuperados. Se não estiverem, a resposta é descartada e o sistema recusa.
- A rota devolve `resposta` e `citacoes` (lei, artigo, url, data de acesso).

Implementação (05/11, tarefas 2.1 e 2.2):
- Rota `POST /juridico` com `{"pergunta"}`, separada de `/mensagem` (a tela passa a usá-la na tarefa 2.4). Devolve `{"resposta", "citacoes", "recusada"}`; cada citação traz `lei`, `artigo`, `citacao` (rótulo para exibir, ex.: "Lei 11.340/2006, art. 7º"), `url` e `data_acesso`. LLM indisponível: 503 com o Ligue 180, como em `/mensagem`.
- Recupera os 5 trechos do eixo `juridico` (decisão de `s2-base-juridica-unificada`). No prompt, cada trecho vai com o rótulo "[Lei 11.340/2006, art. 7º]", e a instrução pede a citação nesse formato, só em português, sem prometer resultado ("o juiz pode conceder", não "você tem direito").
- Verificação de citação (`app/rag/resposta.py`): extrai cada referência a artigo ("art. 7º", "artigo 5", "arts. 18, 19 e 22") e a associa à norma mencionada mais perto no texto (até 80 caracteres; "Lei Maria da Penha" conta como Lei 11.340/2006). A resposta é descartada se citar um artigo não recuperado, um artigo recuperado atribuído a outra norma, uma norma fora da base ou **nenhum** artigo (a spec exige citação em toda resposta jurídica). Descartada, a rota devolve a recusa com o Ligue 180 e a Defensoria Pública do DF, sem nada do texto do LLM. A verificação é por artigo; o inciso citado não é conferido.
- O índice é montado uma vez por processo (`indice_padrao()`) e aquecido em segundo plano quando o servidor sobe: `/saude` responde na hora e uma pergunta que chegue antes aguarda o índice (cerca de 20 s em CPU).
- Alternativa descartada: aceitar respostas sem citação quando o LLM só explica. Contraria a spec e, no teste com o `qwen2.5:7b-instruct`, as respostas sem citação foram justamente as de conteúdo errado (ex.: "o importante é que exista coabitação", o oposto do art. 5º, III).

### Recusa por baixa similaridade
Se a maior similaridade ficar abaixo de um limite, o sistema recusa sem chamar o LLM. O limite inicial é calibrado com as 10 perguntas do teste rápido e algumas perguntas fora do tema.

Calibração (05/11, `e5-base`, eixo `juridico`, similaridade do trecho mais parecido):
- 15 perguntas do tema (as 10 do teste rápido + 5 novas): de 0,818 a 0,863.
- Claramente fora do tema (tempo, bolo, futebol, série, RG, celular): de 0,785 a 0,805.
- "Quase jurídicas": partilha no inventário 0,817, imposto de renda 0,830, multa de trânsito 0,853, dentro da faixa do tema.

**Limite: 0,81.** Recusa as claramente fora do tema e nenhuma do tema; a margem é pequena (0,805 contra 0,818), porque o `e5` comprime as similaridades. As "quase jurídicas" passam do limite e são barradas pela segunda camada: o prompt manda dizer que não sabe, e a resposta sem citação é recusada (com o `qwen2.5:7b-instruct`, as três foram recusadas em duas rodadas). Os testes em `tests/test_indice.py` garantem que 3 perguntas fora do tema são recusadas com o Ligue 180 e a Defensoria sem chamar o LLM, e que as 10 do teste rápido passam do limite. Recalibrar com as 50 perguntas da S3.

### Teste rápido
`tests/perguntas_juridicas.yaml`, com 10 perguntas no estilo das personas e os artigos esperados (ex.: "ele quebrou minhas coisas, isso é violência?" → art. 7º, IV). Meta: o artigo esperado aparece entre os 5 recuperados em pelo menos 9 das 10 perguntas.

## Risks / Trade-offs

- **Modelo de embeddings pesa na memória do deploy**: o `e5-base` usa cerca de 1,1 GB; considerado na escolha da plataforma (`s2-plataforma-base`).
- **Teste rápido pequeno**: 10 perguntas escritas pela equipe podem favorecer um modelo por acaso. A comparação será refeita com as 50 perguntas da S3.
- **Limite de similaridade mal calibrado**: alto demais gera recusas desnecessárias; baixo demais deixa passar respostas fracas. Será recalibrado com as 50 perguntas da S3.
- **Citação certa não garante conteúdo certo**: a verificação confere se o artigo citado foi recuperado, não se a explicação está correta. A precisão jurídica é medida na S3 (LLM juiz + revisão em dupla).
- **Modelo local troca de idioma**: em 05/11, o `qwen2.5:7b-instruct` respondeu em chinês em 1 das 10 perguntas do teste rápido ("a polícia pode tirar ele de casa na hora…", art. 12-C), 5 de 5 vezes, mesmo com a instrução de idioma reforçada e temperatura 0. A citação estava certa, então a verificação aprovou. **Decisão (05/11):** a verificação também recusa respostas fora do português (`em_portugues()`): qualquer letra de outro alfabeto (chinês, cirílico etc.) ou, em texto latino, mais marcas de inglês ou espanhol que de português. Com o Qwen, essa pergunta passa a receber a recusa com o Ligue 180 e a Defensoria até o modelo de produção entrar.
- **Mudanças no HTML do Planalto quebram a ingestão**: o texto processado fica versionado em `dados/leis/` e só é regenerado na revisão mensal.
