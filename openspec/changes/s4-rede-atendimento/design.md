# Design

## Context

Motivação em `proposal.md`. Estado atual:

- `dados/rede_protecao_df.csv` tem 21 serviços (tipos `CMB`, `CEAM`, `DEAM`, `Defensoria`, `Juizado`, `outro`), sem CRAS e sem saúde, servidos por `GET /rede-protecao` sem parâmetros.
- `renderizarLocais()` e `RA_PROXIMAS` (vizinhas de só 7 RAs) estão em `web/app.js`, o arquivo que a frente do chat também vai mexer na S4.
- `web/dados.js` (`RAS_DF`) tem 17 RAs, mais "Outra RA do DF" e "Prefiro não informar". `scripts/validar_dados.py` tem as 35 RAs oficiais (`RAS_OFICIAIS_DF`) e a faixa de CEP do DF (70000-000 a 73699-999). O site escreve "Estrutural (SCIA)", e a lista oficial, "SCIA/Estrutural".
- O orquestrador (`s4-orquestrador-agentes`) devolve `campos.ra` (só valores de `RAS_DF`) e `campos.violencia_sexual_recente` (`true` para recente ou sem tempo dito, `false` para antiga, `null` sem menção).

## Goals / Non-Goals

**Goals:**
- Ordenar serviços por RA ou CEP sem nenhum dado da usuária sair do aparelho.
- Ter CRAS e saúde com fonte e data verificáveis, sem inventar endereço.
- Deixar a rede num arquivo próprio, para não conflitar com a frente do chat.

**Non-Goals:**
- Distância em quilômetros, GPS ou mapa.
- Importar a base inteira do CNES.
- Um hospital único "de referência" para a urgência de violência sexual, porque nenhuma fonte oficial encontrada aponta um.

## Decisions

Decididas pela equipe (sessão de exploração e respostas de 17/11): tabela local de CEP conferida no navegador (depois da consulta aos Correios, só para dizer se o CEP é do DF: opção (a) da seção de riscos), ligação das RAs que faltam à RA mais próxima da lista (na S4, usada para a RA dos serviços), CEP do chat tirado no aparelho, Correios consultados à mão, CRAS curados, saúde pela SES-DF com o CNES e Lei 12.845/2013 na violência sexual recente.

### Tabela de faixas de CEP: `dados/cep_ra_df.csv`
Colunas: `cep_inicio`, `cep_fim`, `fonte_url`, `data_verificacao`. Duas linhas: 70000-000 a 72799-999 e 73000-000 a 73699-999, as faixas "Total do município" de Brasília na Busca Faixa de CEP. Chega ao navegador por `GET /cep-ra`, sem parâmetros, e o service worker a guarda para funcionar sem internet. O nome do arquivo e da rota ficou do plano anterior (CEP → RA), para bater com as issues #74 a #76.

O plano anterior previa uma faixa por RA, com `ra` e `ra_ordenacao`. A consulta de 17/11 mostrou que os Correios não separam o DF por RA, e a equipe escolheu a opção (a) (ver Risks).

**Fonte:** não existe tabela oficial aberta de CEP por RA. Em 17/11/2026 foram consultados os sites da SEDUH, do IPEDF e da Codeplan, sem tabela, e o Geoportal da SEDUH não respondeu. A fonte oficial é a ferramenta **Busca Faixa de CEP dos Correios** (`https://buscacepinter.correios.com.br/app/faixa_cep_uf_localidade/index.php`), por UF e localidade, que exige CAPTCHA e por isso é consultada à mão. Cada linha registra a URL e a data da consulta. A validação aceita o domínio `correios.com.br` só para esta tabela.

Alternativas descartadas: API externa de CEP (ViaCEP etc.), que mandaria o CEP da usuária a terceiros; sites não oficiais de CEP, cujas faixas se contradizem; e a distância real por coordenadas, que exigiria geocodificação.

### RAs que o site não lista
**Uso na S4:** com a opção (a), o CEP não indica a RA, e a RA da usuária vem de `RAS_DF` (perfil, lista ou `campos.ra` do orquestrador). A tabela abaixo vale para a **RA dos serviços**: os CRAS (tarefa 1.4) ficam também em RAs fora da lista do site (ex.: Sol Nascente, Riacho Fundo II), e `ordenar` os trata como a RA da lista em que ordenam. Em `web/rede.js`, ela é `RA_ORDENACAO`, com "SCIA/Estrutural" (nome oficial) ligada a "Estrutural (SCIA)" (nome do site).

As 18 RAs que faltam em `RAS_DF` recebem uma `ra_ordenacao`. Proposta, **a conferir num mapa oficial** de RAs do GDF antes de entrar na tabela:

| RA oficial | Ordena como |
| :--- | :--- |
| Sol Nascente/Pôr do Sol | Ceilândia |
| Vicente Pires | Taguatinga |
| Arniqueira | Águas Claras |
| Cruzeiro, Sudoeste/Octogonal, Lago Sul, Lago Norte, Varjão | Plano Piloto |
| Candangolândia, Park Way, Riacho Fundo | Núcleo Bandeirante |
| Riacho Fundo II, Água Quente | Recanto das Emas |
| SIA | Guará |
| Sobradinho II, Fercal | Sobradinho |
| Jardim Botânico | São Sebastião |
| Arapoanga | Planaltina |

#### Conferência no mapa oficial (tarefa 1.2, 17/11/2026)

**Fonte:** camada "Limite das Regiões Administrativas do Distrito Federal em 2019" (`geonode:Limite_RA_20190`) do Catálogo de Mapas do IPEDF (`https://catalogo.ipe.df.gov.br/layers/geonode:Limite_RA_20190`), com os limites da Lei Complementar 958/2019. Consultada em 17/11/2026 pelo serviço WFS do catálogo. A camada tem 33 RAs: Arapoanga e Água Quente, criadas em dezembro de 2022, ainda não estão nela. A Lei Complementar 1.028/2023 (DODF nº 223, de 01/12/2023) incluiu os mapas dessas duas RAs na LC 958/2019 e substituiu os mapas de Planaltina e do Recanto das Emas, de onde elas saíram.

**Método:** os polígonos foram projetados em SIRGAS 2000 / UTM 23S (EPSG:31983), e duas RAs contam como vizinhas quando a fronteira comum passa de 200 m. O número entre parênteses é o comprimento aproximado da fronteira, em metros.

**Resultado da `ra_ordenacao`:** as 18 ligações propostas estão confirmadas. Em 15 delas, a RA faz fronteira direta com a RA em que ordena. As três exceções são:
- **Varjão** só faz fronteira com o Lago Norte, que ordena como Plano Piloto. A ligação a Plano Piloto continua valendo, pelo Lago Norte.
- **Arapoanga** e **Água Quente** não estão na camada de 2019. Elas ordenam como a RA de onde saíram (Planaltina e Recanto das Emas), segundo a LC 1.028/2023.

| RA oficial | Ordena como | Vizinhas no mapa (fronteira em m) |
| :--- | :--- | :--- |
| Sol Nascente/Pôr do Sol | Ceilândia | **Ceilândia (27.543)**, Samambaia (9.941) |
| Vicente Pires | Taguatinga | **Taguatinga (9.964)**, Estrutural (5.352), Águas Claras (5.322), Plano Piloto (4.667), SIA, Guará |
| Arniqueira | Águas Claras | Park Way (6.972), Taguatinga (3.630), Riacho Fundo, **Águas Claras (2.557)**, Núcleo Bandeirante |
| Cruzeiro | Plano Piloto | Sudoeste/Octogonal, SIA, **Plano Piloto (1.050)** |
| Sudoeste/Octogonal | Plano Piloto | **Plano Piloto (8.057)**, Cruzeiro, SIA |
| Lago Sul | Plano Piloto | **Plano Piloto (38.191)**, Jardim Botânico, Park Way, Candangolândia |
| Lago Norte | Plano Piloto | **Plano Piloto (56.747)**, Paranoá, Sobradinho, Varjão, Itapoã |
| Varjão | Plano Piloto | Lago Norte (8.185), única vizinha |
| Candangolândia | Núcleo Bandeirante | Plano Piloto (3.110), Park Way, **Núcleo Bandeirante (2.941)**, Lago Sul, Guará |
| Park Way | Núcleo Bandeirante | Lago Sul (15.386), Santa Maria (12.513), **Núcleo Bandeirante (10.558)**, Guará, e mais 7 |
| Riacho Fundo | Núcleo Bandeirante | Riacho Fundo II (10.302), Park Way, **Núcleo Bandeirante (2.990)**, Arniqueira, Taguatinga |
| Riacho Fundo II | Recanto das Emas | Riacho Fundo (10.302), **Recanto das Emas (7.396)**, Park Way, Gama, Samambaia, Taguatinga |
| Água Quente | Recanto das Emas | fora da camada de 2019; saiu do Recanto das Emas (LC 1.028/2023) |
| SIA | Guará | Plano Piloto (15.142), **Guará (5.705)**, Estrutural (4.610), Cruzeiro, Vicente Pires, Sudoeste/Octogonal |
| Sobradinho II | Sobradinho | Fercal (32.569), Plano Piloto (21.263), **Sobradinho (16.800)**, Brazlândia |
| Fercal | Sobradinho | Sobradinho II (32.569), **Sobradinho (17.845)**, Planaltina |
| Jardim Botânico | São Sebastião | **São Sebastião (49.764)**, Lago Sul, Paranoá, Santa Maria, Park Way, Plano Piloto |
| Arapoanga | Planaltina | fora da camada de 2019; saiu de Planaltina (LC 1.028/2023) |

Em SIA, Candangolândia, Park Way e Sobradinho II, a RA do site com a maior fronteira não é a escolhida. A escolha continua válida, porque a RA escolhida também faz fronteira. Só muda se a equipe preferir ordenar pela maior fronteira.

**Vizinhas das 17 RAs do site (`VIZINHAS`):** o cálculo é feito no mapa agrupado, em que cada RA fora do site é juntada à sua `ra_ordenacao`. Assim, as vizinhas são coerentes com a ordenação, e uma RA do site que só toca outra pelo Park Way ou pelo Lago Sul também conta. Ordem: maior fronteira primeiro. Fronteiras de menos de 1 km entram, mas por último.

| RA do site | Vizinhas (fronteira em m) |
| :--- | :--- |
| Plano Piloto | Sobradinho (30.197), São Sebastião (25.935), Guará (22.344), Brazlândia (21.109), Núcleo Bandeirante (19.608), Paranoá (12.170), Taguatinga (8.243), Itapoã (5.212), Estrutural (SCIA) (4.327) |
| Ceilândia | Samambaia (33.555), Brazlândia (13.179), Taguatinga (12.220) |
| Taguatinga | Águas Claras (12.338), Ceilândia (12.220), Samambaia (9.334), Brazlândia (8.372), Plano Piloto (8.243), Estrutural (SCIA) (5.352), Guará (4.016), Núcleo Bandeirante (1.158), Recanto das Emas (1.029) |
| Samambaia | Ceilândia (33.555), Recanto das Emas (26.846), Taguatinga (9.334) |
| Gama | Recanto das Emas (38.695), Santa Maria (12.230), Núcleo Bandeirante (2.228) |
| Planaltina | Sobradinho (50.330), Paranoá (48.617), Itapoã (380) |
| Sobradinho | Planaltina (50.330), Plano Piloto (30.197), Itapoã (15.714), Brazlândia (11.468) |
| Brazlândia | Plano Piloto (21.109), Ceilândia (13.179), Sobradinho (11.468), Taguatinga (8.372) |
| Paranoá | São Sebastião (64.136), Planaltina (48.617), Itapoã (13.039), Plano Piloto (12.170) |
| Núcleo Bandeirante | Plano Piloto (19.608), Recanto das Emas (16.852), Águas Claras (15.702), Guará (13.211), Santa Maria (12.513), São Sebastião (7.813), Gama (2.228), Taguatinga (1.158) |
| Santa Maria | Núcleo Bandeirante (12.513), São Sebastião (12.346), Gama (12.230) |
| Recanto das Emas | Gama (38.695), Samambaia (26.846), Núcleo Bandeirante (16.852), Taguatinga (1.029) |
| Águas Claras | Núcleo Bandeirante (15.702), Taguatinga (12.338), Guará (591) |
| Guará | Plano Piloto (22.344), Núcleo Bandeirante (13.211), Estrutural (SCIA) (4.610), Taguatinga (4.016), Águas Claras (591) |
| São Sebastião | Paranoá (64.136), Plano Piloto (25.935), Santa Maria (12.346), Núcleo Bandeirante (7.813) |
| Itapoã | Sobradinho (15.714), Paranoá (13.039), Plano Piloto (5.212), Planaltina (380) |
| Estrutural (SCIA) | Taguatinga (5.352), Guará (4.610), Plano Piloto (4.327) |

**Divergências com o `RA_PROXIMAS` atual de `web/app.js`:** três pares de lá não fazem fronteira no mapa e não devem passar para `VIZINHAS`:
- Águas Claras → Ceilândia;
- Estrutural (SCIA) → Ceilândia;
- Taguatinga → Recanto das Emas, que só faz fronteira de 1 km, pelo Riacho Fundo II. Fica, mas por último.

Os outros pares do `RA_PROXIMAS` estão confirmados.

**Limite da conferência:** fronteira em comum não é distância de viagem. O Plano Piloto, por exemplo, faz fronteira com Brazlândia pela área do Parque Nacional. As vizinhas servem só para ordenar a lista, sempre com o nome real da RA na tela, como já prevê este design.

Se a lista for ampliada, a tela mostra a RA real ("Sol Nascente/Pôr do Sol") e usa a `ra_ordenacao` só para ordenar. Assim a proximidade não se perde, como aconteceria com "Outra RA do DF".

### `web/rede.js`
Funções puras, testadas em QuickJS, usadas pela tela e pelo chat:

- `cepParaRa(cep, tabela)` → `{ dentroDF }`. `true` quando o CEP cai numa das faixas da tabela; `false` fora delas, inclusive de 72800-000 a 72999-999. O nome ficou do plano anterior: a função não devolve RA.
- `tirarCep(texto, tabela)` → `{ texto, dentroDF }`. Encontra `00000-000`, `00.000-000` ou 8 dígitos seguidos e troca por `[CEP]`. `dentroDF` é `null` quando o texto não tem CEP.
- `ordenar(servicos, { ra, violencia_sexual_recente, tipo })` → nova lista, sem mudar a recebida: primeiro a saúde (tipo `Saúde`) quando `violencia_sexual_recente` é `true`; depois os serviços da mesma RA, os de RAs que ordenam como ela (`RA_ORDENACAO`), os das vizinhas (`VIZINHAS`, da maior fronteira para a menor) e o resto. Em cada grupo, os plantões 24 horas vêm primeiro. Sem RA (ou com "Outra RA do DF" e "Prefiro não informar"), os plantões 24 horas vêm primeiro. Com `tipo`, só esse tipo. A opção usa o nome de `campos.violencia_sexual_recente`, como `web/conversa.js` já chama; `violenciaSexualRecente` também é aceito.
- `textoSaude({ ajudando })` (ou `textoSaude(ajudando)`) → explicação fixa com a citação da Lei 12.845/2013 (arts. 1º e 3º, IV, V e § 1º) e a versão em terceira pessoa. O texto diz só o que a lei diz: não fala em boletim de ocorrência, que a lei não menciona.

`renderizarLocais()` continua em `web/app.js`, mas passa a chamar `Rede.ordenar`, e `RA_PROXIMAS` sai de lá. O chat (`s4-orquestrador-agentes`) chama `Rede.tirarCep` antes de montar o pedido e `Rede.ordenar` para a lista curta. Esse é o contrato entre as duas frentes, fechado na terça de manhã.

Alternativa descartada: conferir o CEP no servidor, que exigiria mandar o CEP e contrariaria a decisão de que o servidor nunca recebe nem devolve CEP.

### CEP do DF e a RA
O CEP não indica a RA. Com um CEP do DF, a ordenação usa a RA do perfil. Sem RA no perfil, a tela e o chat pedem a RA e mostram os plantões 24 horas primeiro. Hoje o perfil aceita guardar só o CEP (`web/app.js`, etapa da RA). Nesse caso, a RA também é pedida, e o texto de ajuda da etapa ("usamos somente para ordenar os locais mais próximos") deixa de valer para o CEP; o ajuste do texto entra na tarefa 3.2.

### CEP no chat
O CEP é tirado do texto antes da checagem de risco no servidor e antes do LLM. A checagem de risco no aparelho roda sobre o texto original, para não perder nada. O CEP fica só na memória da página, como o resto da conversa. Se for de fora do DF, o chat responde no aparelho com a cobertura só do DF e o Ligue 180, e a pergunta continua indo ao orquestrador sem o CEP. Se for do DF, a lista curta usa a RA do perfil ou de `campos.ra`.

### CRAS
Fonte: página **Unidades** da Sedes-DF (`https://www.sedes.df.gov.br/unidades/`), publicada em 08/10/2026 e atualizada em 16/11/2026, segundo a própria página. Ela lista 32 CRAS: 31 unidades fixas e o CRAS Móvel. A leitura automática de 17/11 só trouxe um resumo, então **cada linha é digitada e conferida por uma pessoa na página ao vivo**, com a data da conferência. O CRAS Móvel não entra como endereço, porque o atendimento é itinerante: ele aparece como nota. Tipo novo no CSV: `CRAS`.

**Transcrição (tarefa 1.4, 17/11/2026, Rafaella Borges):** as 31 unidades fixas foram transcritas das capturas de tela da página ao vivo, com nome, endereço, horário e telefones como a página publica.
- **CEP:** a página não publica o CEP dos CRAS. Sem fonte, a coluna `cep` fica vazia nesses serviços, e a validação aceita o vazio só no tipo `CRAS`. A tela Onde buscar ajuda (`web/app.js`) ainda mostra "CEP" mesmo vazio; o ajuste entra com a tela, na tarefa 3.2.
- **RA:** a coluna `ra` traz a RA oficial onde a unidade fica. Em quatro casos, o nome ou o endereço da página não dizem a RA oficial diretamente:
  - **CRAS Ceilândia Sol Nascente:** o endereço diz "QNR 02 – Ceilândia", então ficou Ceilândia.
  - **CRAS Fercal:** o endereço diz "Engenho Velho – Sobradinho", mas o Engenho Velho fica na RA Fercal, então ficou Fercal.
  - **CRAS Areal:** o endereço diz "Águas Claras/DF", mas o Areal fica na RA Arniqueira (desde 2019), então ficou Arniqueira.
  - **CRAS Itapoã Parque:** o endereço não diz a RA, então ficou Itapoã.

  Nos quatro casos, as duas RAs possíveis ordenam igual (`RA_ORDENACAO`), então a escolha não muda a ordem da lista.
- **Correção de digitação:** no CRAS Recanto das Emas I, a página escreve "Recanto da Emas"; no CSV ficou "Recanto das Emas".
- **CRAS Móvel (nota):** base administrativa na SEPN Quadra 515, Bloco B, Ed. Espaço 515, Subsolo (-1), Asa Norte; segunda a sexta-feira, exceto feriados, com horário conforme a ação e o local; telefones (61) 3773-7551, 3773-7549, 3773-7547 e 3773-7545. Atende populações rurais, indígenas, quilombolas e de difícil acesso, por isso não entra na lista ordenada por RA.
- **Conferência pela segunda pessoa:** 5 linhas sorteadas (semente 20261117): CRAS Brasília, CRAS Ceilândia P Sul, CRAS Ceilândia Sol Nascente, CRAS Estrutural e CRAS Sobradinho II. _Pendente:_ nome de quem conferiu e data.

### Saúde de referência para violência sexual
- **Quais unidades:** os Centros de Especialidades para Atenção às Pessoas em Situação de Violência Sexual, Familiar e Doméstica (CEPAV) listados na página "Centros de Referência" da SES-DF (`https://saude.df.gov.br/centros-de-referencia`, atualizada em 15/08/2026, segundo a própria página). A descrição do serviço está em `https://info.saude.df.gov.br/busca-saude-cepav/`. A leitura automática só trouxe os nomes, então a lista é conferida por uma pessoa na página.
- **Endereço, telefone e horário:** ficha de cada estabelecimento no CNES (`https://cnes.datasus.gov.br/`), com a competência registrada na coluna nova `competencia_cnes`.
- **Só como pista:** a lista "Flores em Rede" da SES-DF (PDF de 2018) e a lista de CEPAV de 2021. Elas ajudam a achar a unidade no CNES, mas nunca são a fonte do dado exibido, por serem antigas.
- **Urgência:** a Lei 12.845/2013, art. 3º, torna o atendimento imediato obrigatório em todos os hospitais do SUS, com profilaxia da gravidez e das infecções sexualmente transmissíveis (incisos IV e V). Por isso o texto orienta o pronto-socorro de qualquer hospital público, sem apontar um hospital único. Os CEPAV aparecem como acompanhamento depois da urgência.
- Tipo novo no CSV: `Saúde`.

Alternativa descartada: importar o CNES do DF inteiro, que traria milhares de estabelecimentos sem dizer quais atendem violência sexual.

### Texto sobre as 72 horas
A Lei 12.845/2013 garante o atendimento imediato e as profilaxias, mas **não fala em 72 horas**. O prazo vem dos protocolos do Ministério da Saúde. O texto cita a lei para o direito e uma fonte oficial do Ministério da Saúde para o prazo, com URL e data. Se essa fonte não for achada até quinta, o texto diz "procure atendimento o quanto antes: algumas profilaxias só funcionam nos primeiros dias" e cita só a lei, sem o número. Isso muda só o texto, não a spec.

### Dados e validação
`scripts/validar_dados.py` passa a aceitar os tipos `CRAS` e `Saúde`, a exigir `competencia_cnes` nas linhas de `Saúde` e a validar `dados/cep_ra_df.csv`: formato, faixa dentro do DF, `cep_inicio` ≤ `cep_fim`, sem sobreposição e fonte dos Correios com data. A faixa do DF do validador (`CEP_DF_MAX` e a mensagem de erro) passa a ser as duas faixas dos Correios, sem 72800-000 a 72999-999.

## Risks / Trade-offs

- **[A Busca Faixa de CEP pode não separar o DF por RA, se os Correios agruparem várias RAs na localidade "Brasília"]** → Na terça, a primeira consulta confere isso. Se não der para separar, a pessoa registra no design, a busca por CEP fica só como "CEP do DF ou de fora" e a busca por RA continua. A equipe decide na terça se corta a busca por CEP.
  - **Resultado da consulta (tarefa 1.1, 17/11/2026, Rafaella Borges):** a Busca Faixa de CEP (`https://buscacepinter.correios.com.br/app/faixa_cep_uf_localidade/index.php`, UF DF) **não separa o DF por RA**. O DF todo aparece como uma única localidade, "Brasília", em 4 linhas:

    | Localidade | Faixa de CEP | Situação | Tipo de faixa |
    | :--- | :--- | :--- | :--- |
    | Brasília | 70000-000 a 72799-999 | Codificado por logradouros | Total do município |
    | Brasília | 73000-000 a 73699-999 | Codificado por logradouros | Total do município |
    | Brasília | 70000-001 a 72799-999 | Codificada por logradouros | Exclusiva da sede urbana |
    | Brasília | 73000-001 a 73699-999 | Codificada por logradouros | Exclusiva da sede urbana |

    Com essa ferramenta, não dá para montar `dados/cep_ra_df.csv` com uma faixa por RA. Pelo plano deste risco, a busca por CEP fica só como "CEP do DF ou de fora", e a busca por RA continua.
  - **Faixa do DF:** a faixa de **72800-000 a 72999-999 não pertence ao DF**. `scripts/validar_dados.py` (`CEP_DF_MAX` e a mensagem de erro) e o design de `s2-fontes-df` usam 70000-000 a 73699-999 e aceitam esse intervalo como DF. A correção entra na tarefa 1.5, e `cepParaRa` (tarefa 2.1) usa as duas faixas.
  - **Decisão sobre a busca por CEP (17/11/2026): opção (a).** O CEP fica só para dizer se é do DF ou de fora, e a RA vem do perfil ou da lista. Opções descartadas: (b) cortar a busca por CEP da S4; (c) procurar outra fonte oficial de CEP por RA, sem fonte conhecida e com risco para o prazo de quinta. A spec, a proposta, este design e as tarefas 1.3, 1.5, 2.1, 3.1, 3.2 e 5.1 foram ajustados.
- **[Endereços e telefones mudam]** → Fonte e data em cada serviço e recomendação de confirmar por telefone, como já diz a spec.
- **[A ligação de RA para a RA mais próxima é aproximada]** → É só para ordenar, sempre com o nome real exibido e conferida num mapa oficial.
- **[Um número de 8 dígitos que não é CEP some do texto]** → Tirar a mais é o lado seguro. A checagem de risco no aparelho usa o texto original.
- **[A saúde atrasa]** → É o item 3 da ordem de corte da S4. Sem ela, a resposta em violência sexual mantém a explicação da Lei 12.845/2013 e a orientação do pronto-socorro, sem a lista de CEPAV.

## Migration Plan

Os 21 serviços atuais continuam com as mesmas colunas, e `competencia_cnes` fica vazia neles. Para voltar atrás, basta retirar `web/rede.js` e reverter `renderizarLocais()`. `GET /rede-protecao` continua sem parâmetros.

## Open Questions

- Fonte oficial do Ministério da Saúde para o prazo de 72 horas: buscada na quinta. Sem ela, o texto fica sem o número, como descrito acima.
