# Design

## Context

Motivação em `proposal.md`. Estado atual que molda a solução:

- `web/app.js` (`enviar()`) manda só `{pergunta}` para `/juridico`, sem perfil e sem histórico. `/mensagem` aceita histórico, mas o site não a usa.
- Quando `Risco.avaliar` dispara no aparelho, `enviar()` chama `mostrarAlerta()` e retorna: a pergunta que vinha junto nunca é respondida.
- `/juridico` (`app/main.py`) chama `alerta_de_risco()` antes de tudo e devolve só o alerta. Se `/orquestrar` copiar esse padrão, o texto reenviado depois de "Continuar" volta como alerta de novo.
- Benefícios (`web/beneficios.js`, `Beneficios.avaliar`), triagem (`web/triagem.js`, `Triagem.avaliar`) e rede (tela Onde buscar ajuda, `GET /rede-protecao` sem parâmetros) são determinísticos e rodam no navegador. O perfil fica em `web/perfil.js`, e `tests/test_pwa.py` garante que nenhum `fetch` o envia.
- `app/rag/resposta.py` tem `EIXOS`, `INSTRUCOES` e `LIMITE_SIMILARIDADE` fixos; o `/juridico` foi avaliado na S3 com esses valores.
- O log (`app/logs.py`) registra só método, rota, status, duração e tipo de erro.
- `web/dados.js` (`RAS_DF`) tem 17 RAs, mais "Outra RA do DF" e "Prefiro não informar".
- O cliente de LLM (`app/llm.py`) já aceita `temperatura`.

## Goals / Non-Goals

**Goals:**
- Uma rota que classifica e, quando o agente é do servidor, já responde no mesmo pedido.
- O navegador e o servidor trabalham em paralelo desde terça, a partir do contrato abaixo.
- O orquestrador funciona sem `s4-rag-beneficios` e sem `s4-rede-atendimento`.

**Non-Goals:**
- Memória de conversa ou contexto entre mensagens.
- Mudar o `/juridico`, o `/mensagem` ou as specs de privacidade.
- Medir o roteamento contra uma meta: ele é só evidência.

## Decisions

Todas as decisões abaixo foram tomadas pela equipe na sessão de exploração de 17/11, salvo as marcadas como **padrão do planejamento**.

### Contrato do `POST /orquestrar` (fechado na terça de manhã)

Pedido (o modelo recusa campos a mais com 422, então `perfil` ou `historico` nunca são processados):

```json
{ "texto": "1 a 2000 caracteres", "alerta_visto": false, "ajudando": false }
```

Resposta 200:

```json
{
  "risco_imediato": false,
  "categoria_risco": null,
  "alerta": null,
  "agente": "juridico | beneficios | triagem | rede | fora_do_tema | null",
  "tipo": "direito | explicacao | null",
  "campos": { "beneficio": null, "ra": null, "violencia_sexual_recente": null },
  "resposta": { "resposta": "texto", "citacoes": [], "recusada": false, "aviso": null },
  "outras_perguntas": [],
  "excedeu": false,
  "decidido_por": "regra | llm | reserva | null"
}
```

- `risco_imediato: true` sem `alerta_visto`: `alerta` traz o texto de `risco.ALERTA`, e `agente`, `resposta` e `decidido_por` vêm nulos. Nada mais é feito.
- `risco_imediato: true` com `alerta_visto`: resposta completa do agente, com o risco indicado junto.
- `tipo` só é preenchido quando `agente` é `beneficios`.
- `campos.beneficio`: um `id` de `regras/beneficios.json` (`bolsa_familia`, `bpc`, `auxilio_aluguel`, `aluguel_social_df`), `"outro"` quando o texto cita um benefício sem regra, ou `null`.
- `campos.ra`: um valor de `RAS_DF` (sem "Outra RA do DF" e "Prefiro não informar") ou `null`.
- `campos.violencia_sexual_recente`: `true` quando o texto fala de violência sexual recente **ou sem dizer quando** (na dúvida, a saúde vem primeiro, como na triagem conservadora); `false` só quando o texto diz que foi há mais tempo; `null` quando não há menção a violência sexual.
- `resposta`: preenchida para `juridico`, `beneficios` com `tipo: explicacao` e `fora_do_tema`; nula para os agentes do aparelho (`beneficios` com `tipo: direito`, `triagem` e `rede`).
- `resposta.aviso`: só na explicação de benefícios (`s4-rag-beneficios`), com a data da coleta da norma; nulo nos demais.
- `outras_perguntas`: até 2 perguntas reescritas. `excedeu: true` quando havia mais de 3.
- Modelos Pydantic em `app/orquestrador.py`; respostas de exemplo em `tests/orquestrar_exemplos.json`, validadas por `tests/test_orquestrar_contrato.py`.
- Erro do LLM ao gerar a resposta jurídica: 503 com `{"erro": ...}`, como no `/juridico`.

Na terça de manhã, o navegador começa com uma resposta falsa fixa neste formato (um arquivo de exemplos usado só nos testes), sem esperar o servidor. Alternativa descartada: o navegador chamar `/juridico` em um segundo pedido depois da classificação, o que custaria duas viagens e duas checagens de risco.

### Orquestração em duas etapas
1. **Regra** (`regras/roteamento.json`, versionado): listas de palavras por agente, marcas de "tenho direito?", marcas de várias perguntas (2+ "?", "e também", "outra coisa", "além disso" e "e" seguido de palavra interrogativa, como "e onde" ou "e como", para o cenário "o que é medida protetiva e onde eu peço ela?" ir ao LLM) e apelidos do auxílio-aluguel. Ela decide só quando casa exatamente um agente e não há marca de várias perguntas. A comparação é sem acento e em minúsculas, como `risco.py`. Os campos do texto também vêm do arquivo: quando o texto cita dois benefícios ou duas RAs diferentes, o campo fica nulo, e "Sobradinho II" não vira "Sobradinho".
2. **LLM**, com temperatura 0 e uma instrução que lista os cinco agentes, os dois tipos de benefício e o formato JSON de saída: `{"perguntas": [{"agente", "tipo", "pergunta", "beneficio", "ra", "violencia_sexual_recente"}]}`, na ordem em que a usuária escreveu. A saída é validada com Pydantic: agente fora da lista, `tipo` inválido ou JSON quebrado fazem cair na reserva. Cercas de código em volta do JSON são aceitas. Já `beneficio` ou `ra` fora do contrato não invalidam a saída: viram nulos, como diz a spec para a RA fora da lista do site. A instrução fica em `INSTRUCOES_CLASSIFICACAO` (`app/orquestrador.py`), e `classificar()` junta as três etapas.
3. **Reserva**: `juridico` com o texto original. O jurídico já tem a recusa por similaridade e por falta de citação.

Alternativas descartadas: só a regra, que não separa nem reescreve perguntas; só o LLM, que manda todo texto a mais uma chamada externa e fica mais lento; classificar no navegador, que não teria o LLM para separar e reescrever.

### Auxílio-aluguel e Aluguel Social
Na regra: um apelido do auxílio-aluguel ("auxílio-aluguel", "aluguel da Maria da Penha", "aluguel do juiz") com marca de "tenho direito?" vai para `beneficios`/`direito` (`auxilio_aluguel`), e sem essa marca vai para `juridico`, porque a norma (Lei 11.340/2006, art. 23, VI) está no eixo jurídico. "Aluguel social" vai para `beneficios` (`aluguel_social_df`). A instrução do LLM repete essa regra com exemplos.

### Respostas no servidor e no aparelho
- `juridico`: `resposta.responder(...)` com os parâmetros do jurídico e, no modo de ajuda, com `INSTRUCOES_AJUDANDO`.
- `beneficios`/`explicacao`: chama a função de explicação de benefícios, se `s4-rag-beneficios` a registrar; enquanto não existir, chama o jurídico. O orquestrador só conhece um ponto de troca, então cortar o RAG de benefícios não quebra nada.
- `fora_do_tema`: texto fixo com o Ligue 180 e a Defensoria Pública do DF, sem índice e sem LLM de resposta.
- `beneficios`/`direito`, `triagem` e `rede`: o servidor devolve só o agente e os campos; o navegador decide.

Com uma única pergunta, o RAG recebe o texto original. Com várias, recebe a pergunta reescrita. Assim a reescrita não altera a pergunta comum, que é o caso mais frequente. O cliente de LLM é criado só quando uma etapa precisa dele, então a regra e os agentes do aparelho respondem mesmo sem LLM configurado. O ponto de troca é `orquestrador.explicar_beneficio` (`app/orquestrador.py`).

### Parametrizar `responder()` sem mudar o `/juridico`
`responder(pergunta, indice, cliente, *, eixos=EIXOS, instrucoes=INSTRUCOES, limite=LIMITE_SIMILARIDADE)`. Os valores padrão são os da S3, então a chamada do `/juridico` não muda. Pela decisão 18, essa tarefa é a primeira de terça e fica com a frente do RAG de benefícios, porque as duas mudanças mexem no mesmo arquivo. **Padrão do planejamento:** a tarefa fica registrada nesta mudança, e não em `s4-rag-beneficios`, porque o modo de ajuda depende dela e esta mudança não pode depender de outra que é a primeira a ser cortada. Um teste confere que `/juridico` chama `responder` com os mesmos eixos, instruções e limite da S3.

### Várias perguntas e ordem
O LLM separa e reescreve até 3 perguntas, resolvendo pronomes ("onde eu peço ela?" vira "onde peço medida protetiva?"). O servidor ordena com ordenação estável: `triagem` primeiro, depois a ordem escrita (o risco imediato já foi tratado antes). Responde a primeira e devolve as outras em `outras_perguntas`. Com mais de 3, `excedeu: true`: responde a primeira e mostra até 2 sugestões. O navegador mostra as sugestões como botões que enviam a pergunta como mensagem nova.

### Alerta e "Continuar com minha pergunta"
No aparelho: se `Risco.avaliar` disparar, mostra o alerta com o botão e guarda o texto só numa variável em memória. Nada é enviado. O toque reenvia com `alerta_visto: true`. No servidor: `risco.avaliar` roda sempre, primeiro. Sem `alerta_visto`, o servidor devolve só o alerta, igual ao `/juridico`. Com `alerta_visto`, segue para o agente e devolve `risco_imediato: true` junto, e o navegador mostra uma linha de 190 acima da resposta.

`alerta_visto` vem do navegador e **não é controle de segurança**: qualquer cliente pode mandar `true`. A proteção principal é o alerta local, antes do envio. A checagem do servidor existe para versões antigas da página, que não conhecem o botão e por isso nunca mandam a flag. Alternativas descartadas: enviar automaticamente depois do alerta, que mandaria texto de risco ao DeepSeek sem escolha da usuária; e não responder nunca, que é a lacuna atual.

### Modo "ajudando outra pessoa"
Botão de ativar e desativar no cabeçalho do chat, com `aria-pressed`, e estado só em memória: ele não é gravado e volta desligado ao reabrir. O pedido leva só `ajudando: true`. `INSTRUCOES_AJUDANDO` é `INSTRUCOES` mais linhas para a terceira pessoa ("ela"), para como apoiar sem expor a vítima ao agressor e para respeitar a decisão dela. Elas ficam em `app/orquestrador.py`, e não em `app/rag/resposta.py`, porque o `/juridico` nunca as usa. A linha de apoio é a única exceção à regra de usar só os trechos: uma ou duas frases fixas de apoio, sem citar artigo, que a verificação de citação não precisa conferir. Valem também para a explicação de benefícios que cai no jurídico. Os agentes do navegador têm um texto fixo alternativo para o modo de ajuda.

### Módulo do chat no navegador
Um arquivo novo, `web/conversa.js`, com funções puras testadas em QuickJS, como `web/beneficios.js`: montar o pedido e transformar a resposta do servidor (mais o perfil, as regras e os serviços já carregados) em blocos a exibir: alerta, linha de 190, resposta com fontes, cartão de benefício, convite ao formulário, oferta de triagem, lista curta de serviços, sugestões e aviso de excesso. `web/app.js` só desenha os blocos. Assim a lógica é testável e o conflito com a frente da rede em `web/app.js` diminui.

- **Cartão de benefício:** `Beneficios.avaliar(regras, Perfil.paraAvaliacaoBeneficios(perfil), {})`, filtrado por `campos.beneficio` quando houver. Os campos vêm do contrato comum da `s3-beneficios`. As perguntas específicas não respondidas resultam em "faltam informações", com um botão que leva à tela Benefícios. Com `beneficio: "outro"`, o cartão diz que o site avalia só os quatro benefícios e orienta a procurar o CRAS. Sem perfil, o chat convida ao formulário, com 190 e 180 visíveis.
- **Triagem:** botão que abre a tela Avaliação de Risco. A triagem continua só na tela, em memória.
- **Rede:** até 3 serviços de `GET /rede-protecao`, ordenados pela função de ordenação de `s4-rede-atendimento` (`campos.ra`, senão a RA do perfil, e `violencia_sexual_recente`), com um botão para a lista completa. Sem essa função, a ordem é: a mesma RA primeiro, depois os plantões 24 horas. **Padrão do planejamento:** o cartão de rede no chat não exige o formulário, porque quem pede uma delegacia às pressas não deve ser bloqueada. A tela Onde buscar ajuda continua exigindo o formulário, como diz a spec de privacidade.

### Sem memória e apagamento
O pedido nunca leva histórico. As sugestões e o texto que aguarda o "Continuar" ficam em variáveis da página, e `apagarConversa()` (chamada no `pagehide` e em `sair()`) as limpa. `tests/test_pwa.py` passa a conferir isso.

### Registro do roteamento
Uma linha por pedido no logger `rede_lilas.orquestrador`: `roteamento decidido_por=<regra|llm|reserva> agente=<agente>`. Nunca o texto, as perguntas reescritas ou os campos. Um teste com `caplog` envia um texto marcado e confere que ele não aparece.

### Envio ao DeepSeek
Pela decisão de 09/11 (opção c), o texto da pergunta já vai ao DeepSeek no jurídico. Agora ele também vai na classificação, quando a regra não decide. O pedido de classificação leva só o texto e a instrução, e as perguntas reescritas só voltam ao DeepSeek se forem para o jurídico ou para a explicação de benefícios. Nunca vão perfil, respostas de benefícios ou da triagem, histórico ou CEP (que o navegador tira do texto, conforme `s4-rede-atendimento`). Texto com sinal de risco só vai depois do toque em "Continuar".

### Casos e medição
- Arquivos em `avaliacao/conjuntos/s4/`: `elegibilidade.yaml` (20 a 30 perfis; `perfil`, `especificas`, `limite`, `esperado` por benefício com `status` e `fonte`), `triagem.yaml` (`respostas`, `nivel_esperado`, `fonte`) e `roteamento.yaml` (`texto`, `agente_esperado`, `tipo_esperado`). Todos têm `id`, `autor` e `conferencia.revisor`, que precisa ser diferente do autor.
- O relatório registra a ferramenta usada para redigir cada conjunto (Claude ou Codex). O gabarito vem do texto da norma (artigo ou item da portaria), e uma pessoa que não escreveu os casos confere cada um. O nome do revisor fica registrado no conjunto.
- `scripts/validar_conjuntos.py` passa a validar os três arquivos.
- **Conferência de 17/11 (tarefa 5.5):** os três conjuntos foram conferidos por Túlio, que não escreveu os casos. O gabarito de elegibilidade tinha sido redigido a partir da regra medida, e por isso concordava com ela em 80 de 80 pares. Para a acurácia não sair 100% por construção, os 80 pares foram re-derivados do texto das normas pelo Claude, sem consultar o gabarito nem rodar a regra, e só depois comparados por script (`avaliacao/conjuntos/s4/elegibilidade_rederivacao.yaml`). Houve 1 divergência: no e-013 (número de pessoas desconhecido, renda total de R$ 400), o Aluguel Social é "provável" pela Portaria SMDF 49/2026, art. 2º, I, porque a renda total de até 2 SM é critério alternativo à per capita. O gabarito foi corrigido, e a regra fica como está para a medição: o erro dela entra no relatório da S4. Ressalva para o relatório: o Claude já conhecia a regra, então a re-derivação não equivale a uma conferência às cegas feita por uma pessoa.
- A medição roda as funções do navegador em QuickJS, como os testes atuais: elegibilidade por par perfil × benefício (meta ≥ 90%); sensibilidade pelos casos com nível esperado alto ou "não foi possível descartar risco alto", mais `tests/casos_risco.yaml` (meta 100%). O roteamento roda a regra sem LLM e, para os casos que vão ao LLM, o modelo de produção, com nome e data registrados.
- Relatório curto em `docs/Relatório S4 - Sistema multiagentes.md`.

## Risks / Trade-offs

- **[A regra escolhe o agente errado com uma palavra solta]** → Ela só decide com um agente e uma pergunta. Os casos de roteamento cobrem os pares que confundem.
- **[O LLM reescreve mal uma pergunta e muda o sentido]** → Com uma pergunta só, vai o texto original. As reescritas aparecem como sugestões que ela escolhe tocar.
- **[Texto vai ao DeepSeek também para classificar]** → Dentro da decisão de 09/11, só com casos fictícios. A regra evita a chamada nos casos simples.
- **[`alerta_visto` forjado]** → Não é controle de segurança. O alerta local vem antes do envio, e o 190 continua visível acima da resposta.
- **[LLM fora do ar]** → A classificação cai no jurídico, e o 190, a triagem, os benefícios e a rede continuam funcionando no aparelho.
- **[Conflito em `web/app.js` entre as frentes]** → A lógica nova vai para `web/conversa.js`, e a rede vai para um arquivo próprio (`s4-rede-atendimento`).
- **[Casos redigidos com um modelo podem repetir o raciocínio das regras]** → O gabarito vem do texto da norma, com artigo, e é conferido por uma pessoa que não escreveu os casos. O relatório informa a ferramenta e declara a conferência.

## Migration Plan

`/juridico` e `/mensagem` continuam no ar sem mudança. A rodada da S3 continua reproduzível com `/juridico`. A tela passa a usar `/orquestrar` com a nova versão do service worker. Para voltar atrás, basta a constante da rota voltar para `/juridico` e o `alerta_visto` deixar de existir.

## Open Questions

- Quem confere os gabaritos: decidido na terça, 17/11, e registrado no campo `conferencia.revisor` dos conjuntos. Não muda specs nem tarefas.
