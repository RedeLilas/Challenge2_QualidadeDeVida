# Tasks

## 1. Regras e testes (quinta, 05/11)

- [ ] 1.1 Escrever `tests/casos_risco.yaml` com cerca de 30 frases fictícias de risco imediato (todas as categorias) e 30 de não risco; verificação: revisão em dupla das frases
- [x] 1.2 Criar `regras/risco_imediato.json` com as categorias do design; verificação: arquivo validado por teste de estrutura (campos obrigatórios presentes)
- [x] 1.3 Implementar `app/risco.py` (normalização + avaliação); verificação: `uv run pytest tests/test_risco.py` com zero falso negativo
- [x] 1.4 Adicionar teste que rejeita sintaxe de regex não suportada em JS (lookbehind, grupos nomeados)

## 2. Integração (sexta, 06/11)

- [x] 2.1 Chamar `app/risco.py` na rota de mensagem antes do LLM; verificação: teste que envia frase de risco e confirma que o cliente de LLM não foi chamado
- [x] 2.2 Implementar a normalização e a avaliação em `web/app.js` usando o mesmo JSON; verificação manual com 5 frases da suíte, online e offline
- [ ] 2.3 Criar a tela de alerta com `tel:190` e o Ligue 180; verificação: medir no celular o tempo entre enviar e ver o alerta (meta ≤ 2 s)
- [ ] 2.4 Atualizar o status no `ROADMAP.md` e arquivar a mudança
