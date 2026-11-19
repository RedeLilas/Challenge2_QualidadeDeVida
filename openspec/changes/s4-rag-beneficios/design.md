# Design

## Context

Motivação em `proposal.md`. Estado atual, verificado no código:

- `app/rag/resposta.py`: `EIXOS = {"juridico"}`, `LIMITE_SIMILARIDADE = 0.81`, `INSTRUCOES` do jurídico e `verificar_citacoes(texto, recuperados)`, que junta `LEIS_JURIDICAS` aos rótulos dos trechos recuperados.
- `_mencoes_de_leis` reconhece uma norma pelo padrão `Lei (\d+)\.(\d+)/\d{4}$` do rótulo ou pelo rótulo inteiro sem acento. Os rótulos de benefícios são "Lei 8.742/1993 (LOAS)", "Lei Distrital 6.623/2020", "Decreto Distrital 42.376/2021", "Portaria SMDF 49/2026" etc.: o `$` e o prefixo "Distrital" fazem o padrão falhar, e só a cópia exata do rótulo é reconhecida.
- `RE_OUTRA_LEI` lê "Lei 6.623" (sem "Distrital") como norma fora da base, e a resposta é recusada.
- Um artigo sem norma reconhecida perto fica com `lei = None`, e `da_lei` aceita qualquer trecho com aquele número. Com trechos de várias normas de benefícios, "(Decreto 42.376, art. 3º)" é aceito com o art. 3º da Lei 14.601.
- `indice.buscar(pergunta, eixos={...})` já filtra por eixo. As 11 normas de benefícios estão nos eixos `beneficios` (Lei 14.601/2023 e LOAS) e `df` (9 normas distritais).
- Tamanhos desiguais: a LOAS tem 159 trechos, e a Lei Distrital 6.623/2020 tem 3.
- Auxílio-aluguel federal (Lei 11.340/2006, art. 23, VI) está no eixo jurídico. Nos eixos de benefícios, "o que é o auxílio-aluguel?" recupera benefícios eventuais e o Aluguel Social do DF, nunca o art. 23. Por isso o orquestrador manda essa explicação ao jurídico (`s4-orquestrador-agentes`).
- No eixo jurídico, "como funciona o aluguel da maria da penha?" teve similaridade máxima de 0,810, colada no limite de 0,81, com o art. 23 só em 3º lugar.

## Goals / Non-Goals

**Goals:**
- Explicar benefícios com citação conferida, sem duplicar o fluxo do jurídico.
- Corrigir a leitura das normas de benefícios sem mudar nenhum resultado do `/juridico`.
- Calibrar um limite próprio sem contaminar a base da S3.

**Non-Goals:**
- Medir precisão com corretor externo na S4.
- Equilibrar o índice entre normas grandes e pequenas, a menos que o teste de recuperação falhe.
- Levar a Lei 14.737/2023 (eixo `saude`) a qualquer agente.

## Decisions

Todas são decisões da equipe (17/11), salvo as marcadas como **padrão do planejamento**.

### Um fluxo só, com configuração por agente
`responder()` já recebe `eixos`, `instrucoes` e `limite` (tarefa 1.1 de `s4-orquestrador-agentes`). Esta mudança acrescenta a configuração da verificação: as normas aceitas, os apelidos e a regra de recusar artigo sem norma quando há várias normas. Ela fica num objeto de configuração por agente, `JURIDICO` e `BENEFICIOS`, e o `/juridico` passa `JURIDICO`, com os mesmos valores de hoje. Alternativa descartada: copiar `responder()` para um módulo de benefícios, o que deixaria duas cópias da verificação para manter.

### Apelidos das normas de benefícios
Um dicionário de apelidos por rótulo, sem acento e com o ano opcional:

| Rótulo | Apelidos |
| :--- | :--- |
| Lei 14.601/2023 | "lei 14.601", "14601", "bolsa familia" |
| Lei 8.742/1993 (LOAS) | "lei 8.742", "8742", "loas" |
| Lei Distrital 6.623/2020 | "lei (distrital)? 6.623" |
| Decreto Distrital 45.989/2024 | "decreto (distrital)? 45.989" |
| Portaria SMDF 49/2026 | "portaria (smdf)? (n.º)? 49" |
| Lei Distrital 6.938/2021 | "lei (distrital)? 6.938", "cartao gas" |
| Decreto Distrital 42.376/2021 | "decreto (distrital)? 42.376" |
| Lei Distrital 7.009/2021 | "lei (distrital)? 7.009", "prato cheio" |
| Decreto Distrital 42.873/2021 | "decreto (distrital)? 42.873" |
| Lei Distrital 5.165/2013 | "lei (distrital)? 5.165" |
| Decreto Distrital 35.191/2014 | "decreto (distrital)? 35.191" |

Os números aceitam o ponto opcional e "/ano" opcional. Como a menção conhecida cobre o número, `RE_OUTRA_LEI` deixa de marcar "Lei 6.623" como norma de fora. Nomes de programa compartilhados entre lei e decreto (por exemplo, "cartão gás") apontam só para a lei. Quando o LLM citar o decreto, ele usa o número. Os testes cobrem os dois sentidos para cada norma: citação correta aceita e citação de outra norma recusada.

### Artigo sem norma reconhecida
Na configuração `BENEFICIOS`, se `lei` for `None` e os trechos recuperados vierem de mais de uma norma, a citação é recusada. Com uma norma só, o artigo é dela, e a citação é aceita. A configuração `JURIDICO` mantém o comportamento atual, porque a decisão é não mudar o que foi avaliado na S3. Esse caso também existe no jurídico e fica registrado como pendência para a S7, junto com a melhoria da recuperação.

### Instruções de benefícios
`INSTRUCOES_BENEFICIOS` segue o formato de `INSTRUCOES`, com estas mudanças: explica o que a norma prevê sobre o benefício e nunca diz se a pessoa tem direito; indica a tela Benefícios para a avaliação e o CRAS para pedir; cita a norma e o artigo no formato do rótulo; e, se os trechos não bastarem, diz só que não sabe explicar com segurança. A data da coleta não depende do LLM: a resposta traz `data_acesso` em cada citação, como no jurídico, e o servidor acrescenta um `aviso` fixo ("Valores e regras podem mudar por decreto. Norma consultada em DD/MM/AAAA."), com a data mais antiga entre as normas citadas. **Padrão do planejamento:** a data entra no aviso fixo, e não no texto do LLM, para não depender de ele copiar a data certa.

A recusa de benefícios tem texto próprio, que indica o CRAS e o Ligue 180, sem a Defensoria, que é do jurídico.

### Expansão de siglas na busca de benefícios
Nenhum dos 159 trechos da `Lei 8.742/1993` em `dados/leis/` contém a sigla `"BPC"` (todos escrevem `"benefício de prestação continuada"` por extenso, e o rótulo é `"Lei 8.742/1993 (LOAS)"`). Sem expansão, `"o que é o bpc?"` (`bd-005`) tem similaridade de `0,8198` e recupera só trechos de outros programas (`Decreto Distrital 42.376/2021`, `Lei Distrital 6.938/2021`, `Lei 14.601/2023` e `Portaria SMDF 49/2026`); se o LLM respondesse citando um deles, a citação passaria na verificação por estar entre os trechos recuperados.

`app/rag/resposta.py` aplica uma tabela fixa (`SIGLAS_BENEFICIOS`: `\bbpc\b` → `"benefício de prestação continuada (bpc)"`) apenas ao texto enviado a `indice.buscar` em `explicar_beneficio()`, antes do embedding. A pergunta enviada ao LLM continua a original. Conferência das demais siglas leigas do conjunto nos trechos dos eixos `beneficios` e `df`: `"LOAS"` já aparece nos 159 rótulos da `Lei 8.742/1993 (LOAS)` (`"o loas é pra quem?"` tem `0,8470` e `bd-007` tem `0,8641` com a LOAS no top 5), `"CadÚnico"` já aparece em 35 trechos (inclusive na `Lei 14.601/2023, art. 5º`, recuperado em 1º lugar em `bd-004` com `0,8717`; expandir `"cadunico"` para `"Cadastro Único (CadÚnico)"` deslocaria o `art. 5º` do top 5 em favor do `art. 6º-F` da LOAS), `"INSS"` aparece em 9 trechos (`bd-006`, `0,8682`) e `"CRAS"` em 3 trechos. Por isso só `"bpc"` entra na tabela.

### Limite de similaridade próprio
`LIMITE_BENEFICIOS` é calibrado só com as perguntas de desenvolvimento de benefícios, seguindo o método da S3: menor similaridade das perguntas do tema e faixa das extras quase do tema. O 0,81 vale só para o jurídico. Perguntas com o vocabulário da lei dão similaridade alta demais e levariam a um limite alto, que recusaria as perguntas leigas. Por isso o conjunto exige linguagem leiga.

Resultado da calibração em **17/11/2026**, após a expansão de `"bpc"`, com `avaliacao/conjuntos/s4/desenvolvimento_beneficios.yaml` nos eixos `beneficios` e `df`:

| Grupo | Menor | Maior |
| :--- | :--- | :--- |
| 22 perguntas do tema (`perguntas`) | 0,8175 (`bd-013`: `"o vale gas cai todo mes?"`) | 0,8959 (`bd-018`: `"o que sao beneficios eventuais?"`) |
| 8 extras quase do tema (`extras`) | 0,8123 (`bd-x04`: `"o fgts rende quanto por ano?"`) | 0,8629 (`bd-x08`: `"aposentadoria por idade precisa de quantos anos de contribuicao?"`) |
| 3 perguntas fora do tema de `tests/test_indice.py` | 0,7981 (Flamengo) | 0,8227 (previsão do tempo em Brasília, pelo fecho dos decretos distritais) |

Detalhamento das faixas:
- Nas **22 perguntas do tema**, a menor é `bd-013` (`0,8175`, sem o nome oficial do Cartão Gás), seguida de `bd-009` (`0,8431`, `"quem pode pedir o cartao de comida do df?"`) e `bd-008` (`0,8511`, `"como funciona o prato cheio?"`). Com a expansão de `"bpc"`, `bd-005` (`"o que é o bpc?"`) subiu de `0,8198` para `0,8809`.
- Nas **8 extras quase do tema**, as similaridades são `bd-x04` (`0,8123`, FGTS), `bd-x03` (`0,8232`, FGTS), `bd-x06` (`0,8387`, seguro-desemprego), `bd-x02` (`0,8505`, imposto de renda), `bd-x01` (`0,8509`, imposto de renda), `bd-x05` (`0,8520`, seguro-desemprego), `bd-x07` (`0,8561`, aposentadoria) e `bd-x08` (`0,8629`, aposentadoria). As faixas se sobrepõem porque as próprias normas de benefícios mencionam `"aposentadoria"` (`Lei 8.742/1993, art. 20, § 10`), `"seguro-desemprego"` (`Lei 8.742/1993, art. 21-A`) e `"renda"`/`"cadastros"` (`Lei 14.601/2023, art. 9º`).
- Valor escolhido: **`LIMITE_BENEFICIOS = 0,815`**. Nenhuma das 22 perguntas do tema é recusada pelo limite (margem de `0,0025` abaixo de `bd-013` e `0,0281` abaixo de `bd-009`), `bd-x04` (`0,8123`) e duas das três fora do tema (`0,7981` e `0,8002`) são barradas antes de chamar o LLM, e as outras 7 extras quase do tema (`0,8232` a `0,8629`) são recusadas pela segunda camada (verificação de citação com `BENEFICIOS`, quando o LLM informa que não sabe explicar com segurança, cita a legislação externa do tema — como a Lei 8.036/1990 do FGTS ou a Lei 8.213/1991 da aposentadoria — ou cita artigo sem norma reconhecida entre múltiplos diplomas). Subir o limite para `0,84` barraria apenas mais duas extras (`bd-x03` e `bd-x06`), mas recusaria a pergunta leiga `bd-013` (`"o vale gas cai todo mes?"`).
- **Conferência de `bd-j01` (`"como funciona o aluguel da maria da penha?"`) contra o `0,81` do jurídico:** no eixo `juridico`, o trecho mais parecido é `Lei 14.149/2021, art. 3º` com **`0,8097`** (arredondado a `0,810` em três casas, mas abaixo de `0,81` por `0,0003`), seguido de `Lei 14.149/2021, art. 1º` (`0,8080`) e `Lei 11.340/2006, art. 23` em 3º lugar (`0,8008`), porque o art. 23, VI escreve `"auxílio-aluguel"` e não `"aluguel"`. Assim, o limite de `0,81` do jurídico recusa essa formulação sem `"auxílio"` antes do LLM; conforme a regra desta mudança, o `/juridico` e o `0,81` permanecem inalterados, e o caso fica registrado para a melhoria de recuperação na S7. Nos eixos `beneficios` e `df`, a mesma pergunta tem `0,8261` (`Portaria SMDF 49/2026, art. 11`), sem o art. 23 da Lei 11.340/2006, confirmando a decisão de roteá-la para o `juridico`.

### Perguntas de desenvolvimento de benefícios
Arquivo `avaliacao/conjuntos/s4/desenvolvimento_beneficios.yaml`, escrito com o Claude na terça e conferido por uma pessoa que não o escreveu:

- `perguntas`: cerca de 20, cobrindo os seis programas (Bolsa Família, BPC e benefícios eventuais da LOAS, Cartão Prato Cheio, Cartão Gás, Aluguel Social do DF e benefícios eventuais do DF). Cada uma tem `id`, `pergunta`, `autor`, `programa` (um dos seis), `sem_nome_oficial` (verdadeiro ou falso), `resposta_esperada`, `pontos_obrigatorios`, `normas_aceitas` ("Norma, art. N", com a norma e o artigo existentes em `dados/leis/`), `fonte` e `conferencia` (`revisor`, `fonte_conferida`, `status`). O campo se chama `programa`, e não `beneficio`, para não se confundir com os ids de `regras/beneficios.json` do contrato do orquestrador. A validação roda com `uv run python -m scripts.validar_conjuntos beneficios` e só passa depois da conferência.
- `extras`: cerca de 8 quase do tema (imposto de renda, FGTS, seguro-desemprego, aposentadoria), com a categoria `quase_do_tema`.
- `juridico`: "como funciona o aluguel da Maria da Penha?", para conferir se o limite de 0,81 a recusa, sem mexer no jurídico.

Se o RAG de benefícios for medido na S6 ou S7, o conjunto da medição tem de ser outro, congelado antes, como na S3. `scripts/validar_conjuntos.py` confere que ele não repete perguntas do conjunto de desenvolvimento.

### Teste de recuperação
`tests/test_indice.py` ganha um teste por benefício, com perguntas tiradas do conjunto de desenvolvimento, e confere que a norma do benefício aparece no top 5 dos eixos `beneficios` e `df`. Se a Lei Distrital 6.623/2020 (3 trechos) perder sempre para a LOAS (159 trechos), o caso fica registrado. Antes de mexer no índice, a correção é aceitar o Decreto 45.989/2024 e a Portaria 49/2026 como normas do Aluguel Social, que já estão no gabarito do cenário da spec.

Resultado verificado em 17/11 com `avaliacao/conjuntos/s4/desenvolvimento_beneficios.yaml` (22 perguntas nos 6 programas):
- **22 de 22 perguntas** trazem a norma esperada do benefício no top 5 dos eixos `beneficios` e `df` após a expansão de `"bpc"`, e os seis programas passam (`bolsa_familia` 4/4, `bpc` 3/3, `prato_cheio` 3/3, `cartao_gas` 3/3, `aluguel_social_df` 4/4, `beneficios_eventuais` 5/5), além da pergunta do cenário da spec (`"como funciona o aluguel social do DF?"`).
- **Aluguel Social do DF (`aluguel_social_df`):** a `Lei Distrital 6.623/2020` (3 trechos) aparece em 4º lugar em `bd-015` e `bd-017`; em `bd-014`, `bd-016` e `"como funciona o aluguel social do DF?"`, os 5 primeiros trechos vêm da `Portaria SMDF 49/2026` (35 trechos) e do `Decreto Distrital 45.989/2024` (8 trechos) — ela não perde para a LOAS no top 5, mas para as normas regulamentadoras do próprio Aluguel Social.
- **Caso `bd-005` (programa `bpc`, `"o que é o bpc?"`):** sem expansão de sigla, os 5 primeiros trechos eram `Decreto Distrital 42.376/2021, art. 6º` (0,8198), `Lei Distrital 6.938/2021, art. 9º` (0,8198), `Lei 14.601/2023, art. 16` (0,8159), `Lei 14.601/2023, art. 18, § 3º` (0,8144) e `Portaria SMDF 49/2026, art. 25` (0,8132), com a `Lei 8.742/1993 (LOAS)` só em 9º lugar (`art. 21-B`, 0,8083), porque a lei escreve `"benefício de prestação continuada"` por extenso e nunca traz `"BPC"`. Com `expandir_siglas_beneficios` (`"o que é o benefício de prestação continuada (bpc)?"` na busca), os 5 primeiros trechos passam a ser do `art. 20` da `Lei 8.742/1993 (LOAS)` (similaridade máxima `0,8809`), e `test_recuperacao_bpc_sigla_curta_bd_005` passa sem `xfail`.

### Ligação ao orquestrador
A mudança registra a função de explicação no ponto de troca do orquestrador (`s4-orquestrador-agentes`, tarefa 3.2). Se a mudança for cortada, nada mais muda, e a explicação continua indo ao jurídico.

## Risks / Trade-offs

- **[O limite calibrado fica alto e recusa perguntas leigas]** → O conjunto exige apelidos, erros e perguntas sem o nome oficial, e a calibração usa só esse conjunto.
- **[Apelidos amplos demais casam palavras comuns]** → Os apelidos de nome de programa ("prato cheio", "cartão gás") apontam só para a lei. Os testes de recusa de outra norma cobrem cada apelido.
- **[A LOAS domina a busca]** → Teste de recuperação por benefício, com o registro descrito acima.
- **[Testado, não medido]** → O relatório da S4 declara isso, e a medição futura usa um conjunto separado e congelado.
- **[A explicação parece decisão de direito]** → A instrução proíbe isso, os testes conferem a ausência de "direito garantido" e de "você tem direito", e a resposta sempre indica a tela Benefícios.

## Migration Plan

O `/juridico` passa a usar a configuração `JURIDICO`, com os mesmos valores, e `tests/test_juridico.py` continua passando sem mudança. Para voltar atrás, basta tirar o registro no ponto de troca do orquestrador, e a explicação de benefícios volta ao jurídico.

## Verificação manual registrada (19/11/2026, tarefa 4.1)

Servidor local com `deepseek-flash` (sem raciocínio); "como funciona o cartão gás?" feito por Túlio no navegador; as demais pelo `/orquestrar`.
- **"como funciona o cartão gás?":** explicação com a Lei Distrital 6.938/2021 e o Decreto Distrital 42.376/2021 e o aviso da data da norma.
- **"o que é o bpc?":** explicação com a Lei 8.742/1993 (LOAS), art. 20 (a expansão da sigla BPC funciona).
- **Sem o nome oficial, "o governo do df ajuda quando nasce um bebe?":** primeiro falhou (ver abaixo); depois das correções, explica o auxílio-natalidade com a Lei Distrital 5.165/2013, arts. 7º, 8º, 10 e 11.
- **"como saco meu fgts?":** recusa. O LLM classificou como fora do tema, então a recusa é a padrão (Ligue 180 e Defensoria), e não a do RAG de benefícios (CRAS).

**Corrigido no teste:**
- A pergunta do bebê era classificada como "direito" (corrigido no orquestrador; ver o design de `s4-orquestrador-agentes`).
- Depois disso, a resposta correta do DeepSeek foi recusada porque repetia "os critérios do art. 3º", remissão que está dentro do texto do art. 11, e o art. 3º não estava entre os trechos recuperados. `INSTRUCOES_BENEFICIOS` ganhou a regra de não mencionar artigos que só aparecem dentro de outros e o limite de 5 frases curtas (as respostas tinham cerca de 10 frases).
