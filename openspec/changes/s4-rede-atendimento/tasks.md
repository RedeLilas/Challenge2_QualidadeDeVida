# Tasks

## 1. Dados com fonte (terça, 17/11)

- [ ] 1.1 Consultar a Busca Faixa de CEP dos Correios para o DF e conferir se ela separa as faixas por RA; registrar o resultado no design (seção de riscos); verificação: o design registra se a busca separa por RA, e, se não separar, a decisão da equipe sobre a busca por CEP
- [ ] 1.2 Conferir num mapa oficial de RAs do GDF a tabela de `ra_ordenacao` do design e as vizinhas das 17 RAs do site, e registrar a fonte e a data; verificação: o design traz a tabela conferida, com a URL e a data do mapa
- [ ] 1.3 Montar `dados/cep_ra_df.csv` a partir dos Correios, com `ra`, `ra_ordenacao`, `fonte_url` e `data_verificacao` em cada faixa; verificação: `uv run python scripts/validar_dados.py` passa com as regras novas da tarefa 1.5
- [ ] 1.4 Digitar os CRAS da página Unidades da Sedes-DF (31 fixos; o CRAS Móvel como nota) em `dados/rede_protecao_df.csv` com o tipo `CRAS`, conferindo cada linha na página ao vivo; verificação: a validação passa, e uma segunda pessoa confere 5 linhas sorteadas na página
- [ ] 1.5 Ampliar `scripts/validar_dados.py`: tipos `CRAS` e `Saúde`, `competencia_cnes` obrigatória em `Saúde`, e a tabela de CEP (formato, faixa do DF, início ≤ fim, sem sobreposição, 35 RAs, `ra_ordenacao` em `RAS_DF`, domínio `correios.com.br` só nela); verificação: testes em `tests/test_validar_dados.py` cobrem faixa sobreposta, RA sem faixa, `ra_ordenacao` fora da lista e saúde sem competência

## 2. Lógica da rede no navegador (terça, 17/11)

- [ ] 2.1 Criar `web/rede.js` com `cepParaRa`, `tirarCep`, `ordenar`, `VIZINHAS` e `textoSaude`, no contrato do design (fechado com a frente do chat na terça de manhã); verificação: testes em QuickJS cobrem CEP do DF com faixa, CEP do DF sem faixa, CEP de Goiânia, os formatos `00000-000`, `00.000-000` e 8 dígitos, a RA fora do site (Sol Nascente → nome real, ordena como Ceilândia) e a ordem com e sem violência sexual recente
- [ ] 2.2 Escrever o texto de saúde com a Lei 12.845/2013 (arts. 1º e 3º, IV e V), a orientação de pronto-socorro de hospital público e a versão em terceira pessoa; verificação: teste em QuickJS confere a citação, as duas versões e que o texto é condicional ("se foi nas últimas 72 horas")

## 3. Tela e chat (quinta, 19/11)

- [ ] 3.1 Criar `GET /cep-ra` sem parâmetros e incluir a tabela no service worker; verificação: teste confere que a rota não aceita parâmetros, devolve as faixas e que o service worker guarda a rota
- [ ] 3.2 Ligar a tela Onde buscar ajuda a `web/rede.js`, com campo de CEP, nome real da RA, aviso para CEP do DF sem faixa e mensagem do Ligue 180 fora do DF, e tirar `RA_PROXIMAS` de `web/app.js`; verificação: `tests/test_pwa.py` confere que nenhum `fetch` leva CEP e que a tela usa `Rede.ordenar`
- [ ] 3.3 Chamar `Rede.tirarCep` em `enviar()` antes de montar o pedido, depois da checagem de risco local sobre o texto original, e responder no aparelho quando o CEP for de fora do DF (coordenado com a tarefa 4.4 de `s4-orquestrador-agentes`); verificação: teste em QuickJS ou em `tests/test_pwa.py` confere que o corpo do pedido não contém o CEP
- [ ] 3.4 Incluir `web/rede.js` no service worker e na lista de scripts verificados e subir a versão do cache; verificação: `tests/test_pwa.py` confere a lista e que `web/rede.js` não usa armazenamento

## 4. Saúde curada (quinta, 19/11; item 3 da ordem de corte da S4)

- [ ] 4.1 Conferir na página "Centros de Referência" da SES-DF a lista de CEPAV e, para cada um, buscar a ficha no CNES; digitar em `dados/rede_protecao_df.csv` com o tipo `Saúde`, a URL da ficha, a data e a competência; verificação: a validação passa, e uma segunda pessoa confere 3 linhas no CNES
- [ ] 4.2 Buscar a fonte oficial do Ministério da Saúde para o prazo de 72 horas e registrar a URL e a data no design; sem fonte, deixar o texto sem o número, como diz o design; verificação: o design registra a fonte ou a ausência dela, e o teste da tarefa 2.2 confere o texto final

## 5. Fechamento (quinta, 19/11)

- [ ] 5.1 Rodar a suíte de risco/190 e a suíte completa e testar no navegador a busca por RA, por CEP do DF, por CEP de RA fora do site, por CEP de Goiânia e o chat com CEP; verificação: `uv run pytest` passa sem falso negativo, e o teste manual fica registrado no design
- [ ] 5.2 Atualizar o status da mudança no `ROADMAP.md`; verificação: a tabela da S4 mostra o status

## Workflow follow-up

- Arquivar a mudança depois de `openspec validate s4-rede-atendimento` passar e de atualizar o `ROADMAP.md`.
