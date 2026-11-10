# Tasks

## 1. Regras versionadas (sexta, 13/11)

- [x] 1.1 Verificar em fonte oficial o valor vigente do salário mínimo e se os R$ 218 do Bolsa Família foram reajustados, registrando fonte e data; verificação: o registro está em `regras/beneficios.json`
- [x] 1.2 Criar `regras/beneficios.json` com as quatro regras, norma, artigo, início de vigência, data de verificação e textos; verificação: teste confere que toda regra tem esses campos e que nenhum texto usa "direito garantido"

## 2. Avaliação (sexta, 13/11)

- [ ] 2.1 Criar `web/beneficios.js` com o cálculo da renda per capita e a avaliação como função pura, no formato do contrato do design; verificação: testes em QuickJS, com casos fictícios, cobrem o valor no limite, acima do limite, número de pessoas inválido e dado não informado
- [ ] 2.2 Cobrir os resultados de cada benefício; verificação: testes cobrem Bolsa Família sem CadÚnico, BPC por deficiência e por idade, auxílio-aluguel sempre judicial, e Aluguel Social com medida, só com boletim, sem nenhum dos dois, fora do DF e sem necessidade de moradia

## 3. Tela (sexta, 13/11)

- [ ] 3.1 Criar a tela de Benefícios atrás do formulário de `s3-frontend-e-perfil`, com as perguntas específicas só em memória, referência legal, aviso de concessão pelo órgão e orientação para procurar o CRAS mais próximo; verificação: `tests/test_pwa.py` confere que as respostas não são gravadas nem enviadas
- [ ] 3.2 Incluir os novos arquivos no service worker e subir a versão do cache; verificação: `tests/test_pwa.py` confere a lista
- [ ] 3.3 Rodar a suíte de risco/190 e a suíte completa; verificação: `uv run pytest` passa sem falso negativo

## Workflow follow-up

- Atualizar o status no `ROADMAP.md` e arquivar a mudança, depois de `openspec validate s3-beneficios` passar.
