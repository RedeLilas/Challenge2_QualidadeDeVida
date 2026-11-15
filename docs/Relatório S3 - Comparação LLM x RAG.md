# Relatório S3: comparação do LLM com e sem RAG

**Avaliação feita por LLM, sem verificação humana das notas.**

Rodada oficial de 15/11/2026. Mudança `openspec/changes/s3-avaliacao-llm-vs-rag/`.

## Resumo

| | Com RAG | Sem RAG | Meta (só com RAG) |
|---|---|---|---|
| **Precisão** | **16/30 (53,3%)** | **13/30 (43,3%)** | 27/30 (90%): **não atingida** |
| **Afirmações sem suporte na lei** | **3/77 (3,9%)** | **30/127 (23,6%)** | até 5%: **atingida** |

- **Fidelidade:** é a maior diferença entre as versões. Com RAG, 1 em cada 26 afirmações jurídicas não tem apoio no texto da lei. Sem RAG, é quase 1 em cada 4.
- **Precisão:** com RAG, o sistema acerta 3 perguntas a mais, mas fica longe da meta. Com 30 perguntas, essa diferença de 3 não permite dizer que uma versão é mais precisa que a outra (ver "Limitações").
- **Tipo de erro:** é o que mais diferencia as versões.
  - Com RAG, o sistema nunca contradisse o gabarito: os erros são omissões (8) e recusas (6).
  - Sem RAG, o modelo contradisse o gabarito em 7 perguntas. Esse é o erro mais perigoso para quem usa a orientação.

## O que foi comparado

As duas versões usam o mesmo modelo, no mesmo dia, com as mesmas instruções. A única diferença é a regra "Responda usando apenas os trechos" e as duas frases que dependem dela. As instruções usadas estão no `registro.yaml` da rodada.

| | Com RAG | Sem RAG |
|---|---|---|
| Recebe trechos de lei | sim: os 5 mais parecidos (`K = 5`) no eixo jurídico | não |
| Recusa do sistema | sim: similaridade abaixo de 0,81, resposta sem citação conferida ou fora do português | não |
| Pede citação e "não sei" quando não souber | sim | sim |

- **Modelo:** `deepseek-flash`, com raciocínio desligado. No changelog, a versão em vigor era a **DeepSeek-V4.1-Flash-1017** (17/10/2026), conferida em https://api-docs.deepseek.com/updates.
- **Horário:** as duas versões rodaram em 15/11/2026, das 16:42 às 16:45, alternando pergunta a pergunta.
- **Base legal (eixo jurídico):** Lei 11.340/2006, Lei 14.149/2021, Código Penal (artigos escolhidos), Código Civil (art. 1.584) e CPC (art. 699-A).

## Método

### Conjunto
- **Composição:** 30 perguntas do tema, com gabarito, pontos obrigatórios, normas aceitas e fonte, e 10 perguntas extras fora do tema. Todas foram escritas pela equipe e são fictícias.
- **Conferência:** cada gabarito foi conferido no texto da lei por uma segunda pessoa (#19).
- **Distribuição:**
  - violência e quem a lei protege: 5;
  - medidas protetivas: 7;
  - polícia, processo e Defensoria: 4;
  - "isso é crime?": 9;
  - guarda: 2;
  - auxílio-aluguel, Fonar e trabalho: 3.
- **Congelamento:** `oficial.yaml` foi congelado em 15/11/2026, às 16:37, antes da rodada. O SHA-256 é `57abec105819856b0c8fec5e1101cc2e692bfd74c006f5f7be9e5f0dbdf63ffe`.
- **Ajustes:** nenhum ajuste foi feito depois do resultado.
- **Recalibração do limite:** usou só as perguntas de desenvolvimento, separadas do conjunto oficial. O limite ficou em 0,81 (`openspec/changes/s3-base-legal-ampliada/design.md`).

### Correção
- **Corretor:** Gemini 4 Argon (Google), de outra empresa que não a do modelo avaliado. Busca na web e memória ficaram desligadas, e cada envio foi feito numa conversa nova, sem acesso ao repositório.
- **Envios:** quatro, todos em 15/11/2026, com as rubricas de `avaliacao/rubricas/`:

| Envio | Rubrica | Data |
|---|---|---|
| A-precisao | precisão | 15/11/2026 |
| A-fidelidade | fidelidade | 15/11/2026 |
| B-precisao | precisão | 15/11/2026 |
| B-fidelidade | fidelidade | 15/11/2026 |

- **Envios às cegas:**
  - cada pergunta teve uma versão sorteada para o arquivo A e a outra para o B (semente 566655662);
  - os códigos são neutros e não revelam qual versão gerou cada resposta;
  - o mapa ficou fora dos envios até o fim da correção.
- **Precisão:** o corretor recebe a pergunta, o gabarito, os pontos obrigatórios e a resposta. A resposta só é certa com todos os pontos presentes e sem contradição. Uma recusa conta como erro.
- **Fidelidade:** o corretor recebe só a resposta e o texto integral dos artigos citados, sem o gabarito. Ele marca cada afirmação jurídica como com suporte, sem suporte ou fora da base (artigo citado que não está na base). Frases de acolhimento e encaminhamento não contam.
- **Controles:**
  - **respostas erradas de propósito:** 3 por arquivo, escritas pela equipe, que contradizem a lei;
  - **trecho comprobatório:** o corretor copia o trecho que justifica cada marcação.
- **Conferência:** `scripts/conferir.py` aceitou os quatro retornos. Nenhuma linha faltou, nenhum trecho copiado deixou de existir no texto enviado, e o corretor reprovou as 3 respostas erradas de propósito nos 4 arquivos.

## Resultado

| | Com RAG | Sem RAG |
|---|---|---|
| Precisão | 16/30 (53,3%) | 13/30 (43,3%) |
| Afirmações jurídicas avaliadas | 77 | 127 |
| Sem suporte | 3 (3,9%) | 30 (23,6%) |
| Fora da base (contadas à parte) | 0 | 14 |
| Respostas que citam artigo fora da base | 0 | 9 |
| Respostas com citação | 27/30 (90,0%) | 29/30 (96,7%) |
| Recusas do sistema | 3 | 0 |
| Recusas do modelo ("Não sei responder com segurança") | 3 | 6 |

As 3 respostas sem citação na versão com RAG são as 3 recusas do sistema.

### Por categoria (acertos)

| Categoria | Perguntas | Com RAG | Sem RAG |
|---|---|---|---|
| Violência e quem a lei protege | 5 | 4 | 3 |
| Medidas protetivas | 7 | 3 | 2 |
| Polícia, processo e Defensoria | 4 | 3 | 1 |
| "Isso é crime?" | 9 | **2** | **5** |
| Guarda | 2 | 2 | 1 |
| Auxílio-aluguel, Fonar e trabalho | 3 | 2 | 1 |

A versão com RAG ganha em todas as categorias, menos em "isso é crime?".

- **Perguntas com resultado igual:** 7 certas nas duas versões e 8 erradas nas duas.
- **Perguntas em que as versões divergem:**
  - só com RAG certa: 9 (of-003, of-008, of-011, of-012, of-014, of-015, of-017, of-022, of-030);
  - só sem RAG certa: 6 (of-006, of-010, of-025, of-026, of-027, of-028).

### Onde cada versão errou

| Motivo | Com RAG | Sem RAG |
|---|---|---|
| Faltou ponto obrigatório | 8 | 4 |
| Contradisse o gabarito | **0** | **7** |
| Recusa do sistema | 3 | 0 |
| Recusa do modelo | 3 | 6 |
| **Total de erros** | **14** | **17** |

**Com RAG**, a precisão cai por dois motivos:
- **Recuperação:** em 5 das 30 perguntas, nenhum dos artigos aceitos estava entre os 5 trechos recuperados (of-005, of-024, of-025, of-027 e of-028). Quatro delas são da categoria "isso é crime?". Sem o artigo certo, o modelo ou recusou, ou respondeu sem o ponto principal. Esse diagnóstico foi feito depois do resultado, e nenhum parâmetro foi mudado.
- **Recusas:** as 3 recusas do sistema (of-005, of-009 e of-019) tiveram similaridade de 0,843 a 0,872, acima do limite de 0,81. Elas vieram da verificação de citação: o modelo citou artigo que não estava entre os trechos recuperados. Somadas às 3 recusas do modelo, são 6 das 14 respostas erradas.

**Sem RAG**, o modelo responde quase sempre, mas inventa mais:
- contradiz o gabarito em 7 perguntas;
- tem 23,6% das afirmações sem suporte;
- cita artigos que não estão na base em 9 respostas.

## Perguntas extras (fora do tema)

As 10 extras não foram ao corretor e não entram na precisão nem na fidelidade. A classificação abaixo é automática; a leitura da equipe está em `avaliacao/rodadas/2026-11-15-oficial/leitura-extras.md`.

| | Com RAG | Sem RAG |
|---|---|---|
| Recusa do sistema | 9 | 0 |
| Recusa do modelo | 1 | 8 |
| Respondeu | 0 | 2 (of-extra-001 e of-extra-004) |

### Observações da equipe

<!-- PENDENTE (tarefa 5.4): resumo da leitura das 10 extras nas duas versões, escrito pela equipe a partir de leitura-extras.md. -->

## Risco da opção (c): DeepSeek e LGPD

- **Decisão:** a equipe escolheu a opção (c) em 09/11 (`openspec/changes/s2-plataforma-base/design.md`): usar a API oficial do DeepSeek só com casos fictícios durante o projeto, declarando o risco neste relatório.
- **O risco:** a API do DeepSeek processa os dados fora do Brasil, o que é uma transferência internacional (LGPD, art. 33). Em uso real, as mensagens podem conter relatos de violência, que são dados sensíveis.
- **Neste projeto:** todas as perguntas da avaliação são fictícias e nenhuma traz dado de pessoa real. O corretor (Gemini) também recebeu só respostas a casos fictícios.
- **Pendente para uso real:** antes de qualquer uso com pessoas reais, é preciso trocar para uma opção que trate essa transferência:
  - **(a)** anonimizar antes do envio; ou
  - **(b)** usar os pesos abertos em um provedor com política de dados conhecida.

## Limitações

- **Sem revisão humana das notas:** um erro sistemático do corretor pode passar despercebido. Os controles foram as respostas erradas de propósito (todas reprovadas) e os trechos comprobatórios (todos conferidos pelo script).
- **Poucas perguntas:** as versões divergem em 15 perguntas, 9 a favor do RAG e 6 contra. Com tão poucos casos, essa diferença pode ser acaso: o teste de McNemar dá p ≈ 0,61. A diferença de fidelidade (3,9% contra 23,6% sem suporte) é bem maior e consistente com a rodada de desenvolvimento.
- **Uma só rodada e um só corretor:** o nome `deepseek-flash` não fixa uma versão. A versão do changelog está registrada, mas uma nova rodada em outra data pode usar outro modelo.
- **Conjunto escrito pela equipe:** as perguntas e os gabaritos foram escritos e conferidos pela equipe. Não houve validação externa por profissional do direito.

## Mudanças em relação ao método da Semana 1

O documento da Semana 1 (`docs/Challenge 2 - Definições do Projeto Semana 1.md`) previa 50 perguntas e revisão em dupla de 20% das notas. As decisões de 09/11, aceitas pelo grupo em 12/11 (#9), mudaram o método:
- 30 perguntas oficiais e 10 extras;
- correção por um único LLM externo, sem revisão humana das notas, com os controles descritos acima.

## Rodada de desenvolvimento

A rodada de 15/11/2026 com as 15 perguntas de desenvolvimento serviu para testar o fluxo e não entra no resultado. O corretor também aceitou os quatro retornos dela.

| | Com RAG | Sem RAG |
|---|---|---|
| Precisão | 8/15 | 5/15 |
| Afirmações sem suporte | 8/59 (13,6%) | 23/77 (29,9%) |

## Material para auditoria

Tudo está em `avaliacao/rodadas/2026-11-15-oficial/`:
- `registro.yaml`: modelo, versão do changelog, data, horário, hash do congelamento e instruções de cada versão;
- `respostas.yaml`: as respostas das duas versões;
- `envios/`: os quatro arquivos enviados e o texto de cada código;
- `mapa.yaml`: a versão por trás de cada código e a semente;
- `retornos/`: os quatro retornos do corretor e o modelo e a data de cada envio;
- `resultado.yaml`: o resultado da conferência.

As rubricas estão em `avaliacao/rubricas/` e o conjunto congelado em `avaliacao/conjuntos/oficial.yaml`.

## Anexo: resultado por pergunta

| Pergunta | Categoria | Com RAG | Sem RAG |
|---|---|---|---|
| of-001 | violência e proteção | certa | certa |
| of-002 | violência e proteção | certa | certa |
| of-003 | violência e proteção | certa | faltou ponto |
| of-004 | violência e proteção | certa | certa |
| of-005 | violência e proteção | recusa do sistema | faltou ponto |
| of-006 | medidas protetivas | faltou ponto | certa |
| of-007 | medidas protetivas | faltou ponto | contradiz |
| of-008 | medidas protetivas | certa | recusa do modelo |
| of-009 | medidas protetivas | recusa do sistema | recusa do modelo |
| of-010 | medidas protetivas | faltou ponto | certa |
| of-011 | medidas protetivas | certa | recusa do modelo |
| of-012 | medidas protetivas | certa | recusa do modelo |
| of-013 | polícia, processo e Defensoria | certa | certa |
| of-014 | polícia, processo e Defensoria | certa | recusa do modelo |
| of-015 | polícia, processo e Defensoria | certa | faltou ponto |
| of-016 | polícia, processo e Defensoria | faltou ponto | contradiz |
| of-017 | auxílio, Fonar e trabalho | certa | contradiz |
| of-018 | auxílio, Fonar e trabalho | certa | certa |
| of-019 | auxílio, Fonar e trabalho | recusa do sistema | faltou ponto |
| of-020 | crime | certa | certa |
| of-021 | crime | faltou ponto | contradiz |
| of-022 | crime | certa | contradiz |
| of-023 | crime | recusa do modelo | contradiz |
| of-024 | crime | faltou ponto | contradiz |
| of-025 | crime | recusa do modelo | certa |
| of-026 | crime | faltou ponto | certa |
| of-027 | crime | faltou ponto | certa |
| of-028 | crime | recusa do modelo | certa |
| of-029 | guarda | certa | certa |
| of-030 | guarda | certa | recusa do modelo |
