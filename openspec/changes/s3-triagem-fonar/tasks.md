# Tasks

## 1. Conferência da fonte (terça, 10/11)

- [ ] 1.1 Abrir o PDF oficial do Fonar (link em `dados/fonar/notas.md`) e registrar em `dados/fonar/notas.md` se ele define níveis de risco; verificação: o registro traz a data e a resposta. Se houver níveis oficiais, parar e ajustar esta mudança antes das próximas tarefas

## 2. Regras e avaliação (até quinta, 12/11)

- [ ] 2.1 Criar `regras/triagem_fonar.json` com as 13 perguntas, opções, efeitos, versão e fonte, seguindo a numeração de `dados/fonar/notas.md`; verificação: teste confere a ordem, o limite de 13 e que cada item citado na spec existe
- [ ] 2.2 Criar `web/triagem.js` com a avaliação como função pura; verificação: testes em QuickJS cobrem cada gatilho, pulo e "não sei" em cada gatilho, encerramento no primeiro gatilho e pulo em pergunta de atenção
- [ ] 2.3 Cobrir a ausência de "risco baixo" e o aviso de limite; verificação: teste confere que todos os resultados têm o aviso e o Ligue 180 e que nenhum texto usa "risco baixo"

## 3. Tela e funcionamento offline (até quinta, 12/11)

- [ ] 3.1 Criar a tela da triagem na navegação de `s3-frontend-e-perfil`, com as respostas só em memória; verificação: `tests/test_pwa.py` confere que a tela não grava no aparelho e não envia requisição com as respostas
- [ ] 3.2 Incluir os novos arquivos no service worker e subir a versão do cache; verificação: `tests/test_pwa.py` confere a lista, e a triagem abre sem internet na verificação manual
- [ ] 3.3 Conferir a saída rápida durante a triagem; verificação manual: tocar em Sair no meio da triagem, voltar e confirmar que as respostas não reaparecem
- [ ] 3.4 Rodar a suíte de risco/190 e a suíte completa; verificação: `uv run pytest` passa sem falso negativo

## Workflow follow-up

- Atualizar o status no `ROADMAP.md` e arquivar a mudança, depois de `openspec validate s3-triagem-fonar` passar.
