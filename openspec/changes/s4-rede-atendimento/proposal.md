# Proposal

## Why

A tela Onde buscar ajuda lista 21 serviços de `dados/rede_protecao_df.csv`, sem CRAS e sem serviços de saúde, e só ordena pela RA do perfil, entre as 17 que o site conhece. A spec `rede-atendimento` pede busca por CEP, rede de saúde para violência sexual e a priorização em até 72 horas. A `s3-beneficios` deixou a lista de CRAS para a S4. Agora o orquestrador (`s4-orquestrador-agentes`) também passa a mandar perguntas de rede para o aparelho, com a RA e o sinal de violência sexual recente tirados do texto.

Métrica do ROADMAP: nenhuma meta da S4 depende diretamente desta mudança. Ela entra no entregável "sistema multiagentes" como o agente de rede, e os serviços de saúde são o item 3 da ordem de corte da S4.

## What Changes

- CEP → RA por uma tabela local de faixas de CEP do DF, montada à mão a partir da Busca Faixa de CEP dos Correios, com fonte e data, e convertida **no navegador**. O servidor nunca recebe nem devolve CEP. A "distância aproximada" passa a ser pela RA.
- A tabela cobre as 35 RAs. Cada RA que não está entre as 17 do site é ligada à RA da lista mais próxima, só para ordenar, e a tela mostra o nome real (ex.: Sol Nascente → ordena como Ceilândia).
- CEP digitado no chat: o navegador encontra o CEP no texto, converte em RA no aparelho e o troca por um marcador antes de enviar. Nenhum CEP chega ao servidor ou ao DeepSeek.
- Lista curada de CRAS do DF, com a página de unidades da Sedes-DF como fonte e data.
- Serviços de saúde de referência para violência sexual curados à mão: os nomes vêm da página da SES-DF, e o endereço e o telefone, da ficha do CNES, com a competência como data. Para a urgência, a orientação é o pronto-socorro de qualquer hospital da rede pública, sem apontar um hospital único sem fonte.
- Ordenação pelos campos do texto (`ra`, `violencia_sexual_recente`) vindos do orquestrador. Com violência sexual recente, a saúde vem primeiro, com a explicação do atendimento rápido e da Lei 12.845/2013 (Lei do Minuto Seguinte).
- Fora do DF: continua como na spec (lista só do DF e indicação do Ligue 180).
- A lógica da rede vai para um arquivo próprio do navegador (`web/rede.js`), fora de `web/app.js`.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `rede-atendimento`: a busca por CEP passa a ser por tabela local de faixas e pela RA; o CEP fica no aparelho, inclusive quando digitado no chat; a base passa a ter a lista de CRAS e a saúde curada com o CNES como fonte; a priorização da saúde em violência sexual recente cita a Lei 12.845/2013.

## Impact

- **Arquivos novos:** `dados/cep_ra_df.csv` (faixas, RA real, RA usada para ordenar, fonte, data), `web/rede.js`, testes em QuickJS.
- **Arquivos alterados:** `dados/rede_protecao_df.csv` (novos tipos `CRAS` e `Saúde`, competência do CNES), `scripts/validar_dados.py`, `web/app.js` (a tela passa a usar `web/rede.js`; `RA_PROXIMAS` sai de lá), `web/index.html` (campo de CEP na tela), `web/sw.js`, `tests/test_pwa.py`, `tests/test_validar_dados.py`.
- **Depende de:** `s4-orquestrador-agentes` para os campos do texto e para a chamada em `enviar()`. A tela funciona sem o orquestrador.
- **Privacidade (LGPD):** o CEP do perfil ou digitado na tela ou no chat é convertido no aparelho, e nenhuma requisição o contém. A tabela chega por uma rota GET sem parâmetros, como a lista de serviços. Nenhuma spec de privacidade muda.
- **Segurança da usuária:** todo serviço mostra a fonte, a data e a recomendação de confirmar por telefone. Endereço desatualizado pode levar a um deslocamento perdido, então a data fica visível. Em violência sexual recente, a orientação de urgência aparece antes da lista.
- **Fora desta mudança:** importar o CNES inteiro, mapa e geolocalização por GPS, cálculo de distância real, serviços fora do DF, a tela de Benefícios apontar o CRAS da RA (continua "procure o CRAS mais próximo") e o cartão de rede no chat, que é de `s4-orquestrador-agentes`.
