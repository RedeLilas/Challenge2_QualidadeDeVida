# Tasks

## 1. Dados com fonte (terça, 17/11)

- [x] 1.1 Consultar a Busca Faixa de CEP dos Correios para o DF e conferir se ela separa as faixas por RA; registrar o resultado no design (seção de riscos); verificação: o design registra se a busca separa por RA, e, se não separar, a decisão da equipe sobre a busca por CEP
- [x] 1.2 Conferir num mapa oficial de RAs do GDF a tabela de `ra_ordenacao` do design e as vizinhas das 17 RAs do site, e registrar a fonte e a data; verificação: o design traz a tabela conferida, com a URL e a data do mapa
- [ ] 1.3 Montar `dados/cep_ra_df.csv` com as duas faixas do DF da Busca Faixa de CEP dos Correios (70000-000 a 72799-999 e 73000-000 a 73699-999), com `fonte_url` e `data_verificacao` em cada faixa, sem RA (opção (a) de 17/11); verificação: `uv run python scripts/validar_dados.py` passa com as regras novas da tarefa 1.5
- [ ] 1.4 Digitar os CRAS da página Unidades da Sedes-DF (31 fixos; o CRAS Móvel como nota) em `dados/rede_protecao_df.csv` com o tipo `CRAS`, conferindo cada linha na página ao vivo; verificação: a validação passa, e uma segunda pessoa confere 5 linhas sorteadas na página
- [ ] 1.5 Ampliar `scripts/validar_dados.py`: tipos `CRAS` e `Saúde`, `competencia_cnes` obrigatória em `Saúde`, a tabela de CEP (formato, faixa dentro do DF, início ≤ fim, sem sobreposição, domínio `correios.com.br` só nela) e a faixa do DF do validador, que passa a ser as duas faixas dos Correios, sem 72800-000 a 72999-999; verificação: testes em `tests/test_validar_dados.py` cobrem faixa sobreposta, faixa fora do DF (72800-000), CEP de serviço entre as duas faixas e saúde sem competência

## 2. Lógica da rede no navegador (terça, 17/11)

- [ ] 2.1 Criar `web/rede.js` com `cepParaRa`, `tirarCep`, `ordenar`, `VIZINHAS` e `textoSaude`, no contrato do design (fechado com a frente do chat na terça de manhã); verificação: testes em QuickJS cobrem CEP de cada uma das duas faixas do DF, 72800-000 como fora do DF, CEP de Goiânia, os formatos `00000-000`, `00.000-000` e 8 dígitos, texto sem CEP (`dentroDF: null`) e a ordem com e sem violência sexual recente
- [ ] 2.2 Escrever o texto de saúde com a Lei 12.845/2013 (arts. 1º e 3º, IV e V), a orientação de pronto-socorro de hospital público e a versão em terceira pessoa; verificação: teste em QuickJS confere a citação, as duas versões e que o texto é condicional ("se foi nas últimas 72 horas")

## 3. Tela e chat (quinta, 19/11)

- [ ] 3.1 Criar `GET /cep-ra` sem parâmetros e incluir a tabela no service worker; verificação: teste confere que a rota não aceita parâmetros, devolve as duas faixas do DF e que o service worker guarda a rota
- [ ] 3.2 Ligar a tela Onde buscar ajuda a `web/rede.js`, com campo de CEP que só confere se é do DF: CEP do DF ordena pela RA do perfil ou pede a RA (com os plantões 24 horas primeiro), e CEP de fora mostra o Ligue 180; ajustar o texto de ajuda da etapa de RA do perfil, que hoje diz que o CEP ordena os locais; e tirar `RA_PROXIMAS` de `web/app.js`; verificação: `tests/test_pwa.py` confere que nenhum `fetch` leva CEP e que a tela usa `Rede.ordenar`
- [ ] 3.3 Chamar `Rede.tirarCep` em `enviar()` antes de montar o pedido, depois da checagem de risco local sobre o texto original, e responder no aparelho quando o CEP for de fora do DF (coordenado com a tarefa 4.4 de `s4-orquestrador-agentes`); verificação: teste em QuickJS ou em `tests/test_pwa.py` confere que o corpo do pedido não contém o CEP
- [ ] 3.4 Incluir `web/rede.js` no service worker e na lista de scripts verificados e subir a versão do cache; verificação: `tests/test_pwa.py` confere a lista e que `web/rede.js` não usa armazenamento

## 4. Saúde curada (quinta, 19/11; item 3 da ordem de corte da S4)

- [ ] 4.1 Conferir na página "Centros de Referência" da SES-DF a lista de CEPAV e, para cada um, buscar a ficha no CNES; digitar em `dados/rede_protecao_df.csv` com o tipo `Saúde`, a URL da ficha, a data e a competência; verificação: a validação passa, e uma segunda pessoa confere 3 linhas no CNES
- [ ] 4.2 Buscar a fonte oficial do Ministério da Saúde para o prazo de 72 horas e registrar a URL e a data no design; sem fonte, deixar o texto sem o número, como diz o design; verificação: o design registra a fonte ou a ausência dela, e o teste da tarefa 2.2 confere o texto final

## 5. Fechamento (quinta, 19/11)

- [ ] 5.1 Rodar a suíte de risco/190 e a suíte completa e testar no navegador a busca por RA, por CEP do DF com e sem RA no perfil, por CEP de Goiânia, por 72800-000 e o chat com CEP; verificação: `uv run pytest` passa sem falso negativo, e o teste manual fica registrado no design
- [ ] 5.2 Atualizar o status da mudança no `ROADMAP.md`; verificação: a tabela da S4 mostra o status

## Workflow follow-up

- Arquivar a mudança depois de `openspec validate s4-rede-atendimento` passar e de atualizar o `ROADMAP.md`.
