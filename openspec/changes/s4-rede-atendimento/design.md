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

Decididas pela equipe (sessão de exploração e respostas de 17/11): tabela local de CEP convertida no navegador, ligação das RAs que faltam à RA mais próxima da lista, CEP do chat tirado no aparelho, Correios consultados à mão, CRAS curados, saúde pela SES-DF com o CNES e Lei 12.845/2013 na violência sexual recente.

### Tabela de faixas de CEP: `dados/cep_ra_df.csv`
Colunas: `cep_inicio`, `cep_fim`, `ra` (nome oficial, uma das 35), `ra_ordenacao` (um valor de `RAS_DF`), `fonte_url`, `data_verificacao`. Chega ao navegador por `GET /cep-ra`, sem parâmetros, e o service worker a guarda para funcionar sem internet.

**Fonte:** não existe tabela oficial aberta de CEP por RA. Em 17/11/2026 foram consultados os sites da SEDUH, do IPEDF e da Codeplan, sem tabela, e o Geoportal da SEDUH não respondeu. A fonte oficial é a ferramenta **Busca Faixa de CEP dos Correios** (`https://buscacepinter.correios.com.br/app/faixa_cep_uf_localidade/index.php`), por UF e localidade, que exige CAPTCHA e por isso é consultada à mão. Cada linha registra a URL e a data da consulta. A validação aceita o domínio `correios.com.br` só para esta tabela.

Alternativas descartadas: API externa de CEP (ViaCEP etc.), que mandaria o CEP da usuária a terceiros; sites não oficiais de CEP, cujas faixas se contradizem; e a distância real por coordenadas, que exigiria geocodificação.

### RAs que o site não lista
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

A tela mostra a RA real ("Sol Nascente/Pôr do Sol") e usa a `ra_ordenacao` só para ordenar. Assim a proximidade não se perde, como aconteceria com "Outra RA do DF".

### `web/rede.js`
Funções puras, testadas em QuickJS, usadas pela tela e pelo chat:

- `cepParaRa(cep, tabela)` → `{ dentroDF, ra, raOrdenacao }`. Se o CEP estiver fora da faixa do DF, `dentroDF: false`. Se estiver no DF e em nenhuma faixa, `ra: null`.
- `tirarCep(texto, tabela)` → `{ texto, local }`. Encontra `00000-000`, `00.000-000` ou 8 dígitos seguidos e troca por `[CEP]`. `local` é o resultado de `cepParaRa`.
- `ordenar(servicos, { ra, violenciaSexualRecente, tipo })` → primeiro a saúde quando `violenciaSexualRecente` é `true`, depois a mesma RA, depois as vizinhas (`VIZINHAS`, para as 17 RAs, a conferir no mesmo mapa) e depois os plantões 24 horas.
- `textoSaude(ajudando)` → explicação fixa com a citação da Lei 12.845/2013 e a versão em terceira pessoa.

`renderizarLocais()` continua em `web/app.js`, mas passa a chamar `Rede.ordenar`, e `RA_PROXIMAS` sai de lá. O chat (`s4-orquestrador-agentes`) chama `Rede.tirarCep` antes de montar o pedido e `Rede.ordenar` para a lista curta. Esse é o contrato entre as duas frentes, fechado na terça de manhã.

Alternativa descartada: converter o CEP no servidor, que exigiria mandar o CEP e contrariaria a decisão de que o servidor nunca recebe nem devolve CEP.

### CEP no chat
O CEP é tirado do texto antes da checagem de risco no servidor e antes do LLM. A checagem de risco no aparelho roda sobre o texto original, para não perder nada. O CEP fica só na memória da página, como o resto da conversa. Se for de fora do DF, o chat responde no aparelho com a cobertura só do DF e o Ligue 180, e a pergunta continua indo ao orquestrador sem o CEP.

### CRAS
Fonte: página **Unidades** da Sedes-DF (`https://www.sedes.df.gov.br/unidades/`), publicada em 08/10/2026 e atualizada em 16/11/2026, segundo a própria página. Ela lista 32 CRAS: 31 unidades fixas e o CRAS Móvel. A leitura automática de 17/11 só trouxe um resumo, então **cada linha é digitada e conferida por uma pessoa na página ao vivo**, com a data da conferência. O CRAS Móvel não entra como endereço, porque o atendimento é itinerante: ele aparece como nota. Tipo novo no CSV: `CRAS`.

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
`scripts/validar_dados.py` passa a aceitar os tipos `CRAS` e `Saúde`, a exigir `competencia_cnes` nas linhas de `Saúde` e a validar `dados/cep_ra_df.csv`: formato, faixa dentro do DF, `cep_inicio` ≤ `cep_fim`, sem sobreposição, as 35 RAs cobertas, `ra_ordenacao` em `RAS_DF` e fonte com data.

## Risks / Trade-offs

- **[A Busca Faixa de CEP pode não separar o DF por RA, se os Correios agruparem várias RAs na localidade "Brasília"]** → Na terça, a primeira consulta confere isso. Se não der para separar, a pessoa registra no design, a busca por CEP fica só como "CEP do DF ou de fora" e a busca por RA continua. A equipe decide na terça se corta a busca por CEP.
- **[Endereços e telefones mudam]** → Fonte e data em cada serviço e recomendação de confirmar por telefone, como já diz a spec.
- **[A ligação de RA para a RA mais próxima é aproximada]** → É só para ordenar, sempre com o nome real exibido e conferida num mapa oficial.
- **[Um número de 8 dígitos que não é CEP some do texto]** → Tirar a mais é o lado seguro. A checagem de risco no aparelho usa o texto original.
- **[A saúde atrasa]** → É o item 3 da ordem de corte da S4. Sem ela, a resposta em violência sexual mantém a explicação da Lei 12.845/2013 e a orientação do pronto-socorro, sem a lista de CEPAV.

## Migration Plan

Os 21 serviços atuais continuam com as mesmas colunas, e `competencia_cnes` fica vazia neles. Para voltar atrás, basta retirar `web/rede.js` e reverter `renderizarLocais()`. `GET /rede-protecao` continua sem parâmetros.

## Open Questions

- Fonte oficial do Ministério da Saúde para o prazo de 72 horas: buscada na quinta. Sem ela, o texto fica sem o número, como descrito acima.
