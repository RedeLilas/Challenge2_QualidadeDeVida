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

### Limite de similaridade próprio
`LIMITE_BENEFICIOS` é calibrado na quinta, só com as perguntas de desenvolvimento de benefícios, seguindo o método da S3: menor similaridade das perguntas do tema e faixa das extras quase do tema. O valor, as faixas e a data ficam registrados nesta seção depois da calibração. O 0,81 vale só para o jurídico. Perguntas com o vocabulário da lei dão similaridade alta demais e levariam a um limite alto, que recusaria as perguntas leigas. Por isso o conjunto exige linguagem leiga.

### Perguntas de desenvolvimento de benefícios
Arquivo `avaliacao/conjuntos/s4/desenvolvimento_beneficios.yaml`, escrito com o Claude na terça e conferido por uma pessoa que não o escreveu:

- `perguntas`: cerca de 20, cobrindo os seis programas (Bolsa Família, BPC e benefícios eventuais da LOAS, Cartão Prato Cheio, Cartão Gás, Aluguel Social do DF e benefícios eventuais do DF). Cada uma tem `id`, `pergunta`, `autor`, `beneficio`, `sem_nome_oficial` (verdadeiro ou falso), `resposta_esperada`, `normas_aceitas` (norma e artigo), `fonte` e `conferencia.revisor`.
- `extras`: cerca de 8 quase do tema (imposto de renda, FGTS, seguro-desemprego, aposentadoria), com a categoria `quase_do_tema`.
- `juridico`: "como funciona o aluguel da Maria da Penha?", para conferir se o limite de 0,81 a recusa, sem mexer no jurídico.

Se o RAG de benefícios for medido na S6 ou S7, o conjunto da medição tem de ser outro, congelado antes, como na S3. `scripts/validar_conjuntos.py` confere que ele não repete perguntas do conjunto de desenvolvimento.

### Teste de recuperação
`tests/test_indice.py` ganha um teste por benefício, com perguntas tiradas do conjunto de desenvolvimento, e confere que a norma do benefício aparece no top 5 dos eixos `beneficios` e `df`. Se a Lei Distrital 6.623/2020 (3 trechos) perder sempre para a LOAS (159 trechos), o caso fica registrado. Antes de mexer no índice, a correção é aceitar o Decreto 45.989/2024 e a Portaria 49/2026 como normas do Aluguel Social, que já estão no gabarito do cenário da spec.

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
