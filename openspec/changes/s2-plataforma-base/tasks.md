# Tasks

## 1. Esqueleto do backend (quinta, 05/11)

- [x] 1.1 Criar o projeto com `uv` (FastAPI, uvicorn, openai, pytest) e a estrutura `app/`, `web/`, `regras/`, `dados/`, `tests/`; verificação: `uv run pytest` passa com um teste de saúde (`GET /saude` → 200)
- [x] 1.2 Criar `app/config.py` lendo `LLM_BASE_URL`, `LLM_MODEL` e `LLM_API_KEY`, e `.env.example` sem valores reais; verificação: teste que falha com mensagem clara se a variável faltar
- [ ] 1.3 Criar `app/llm.py` com o cliente único e rodar contra o Ollama local; verificação: teste com cliente simulado + uma chamada manual ao modelo local
- [x] 1.4 Criar o middleware de log sem conteúdo; verificação: teste que envia uma mensagem e confirma que o texto não aparece no log

## 2. PWA mínima (quinta, 05/11)

- [ ] 2.1 Criar `web/index.html`, `app.js` e `styles.css` com a tela de conversa servida pelo FastAPI; verificação: a página abre em `/` e envia uma mensagem ao backend
- [ ] 2.2 Implementar a saída rápida com `location.replace()` e a conversa só em memória; verificação manual: tocar em "sair" e confirmar que o botão voltar não reabre a conversa e que nada aparece no `localStorage`
- [ ] 2.3 Criar `manifest.webmanifest` (nome e ícone provisórios discretos) e `sw.js` com cache da interface; verificação: o Chrome oferece a instalação e a interface abre offline

## 3. Deploy e CI (sexta, 06/11)

- [ ] 3.1 Escrever o `Dockerfile` e rodar o container localmente; verificação: `docker run` responde em `/saude`
- [ ] 3.2 Criar o workflow de CI com `uv run pytest` (passa a rodar quando o repositório estiver no GitHub)
- [ ] 3.3 Publicar na plataforma escolhida; verificação: a URL de teste abre a PWA no celular

## 4. Decisões da S2 (sexta, 06/11)

- [ ] 4.1 Decidir a plataforma de deploy e registrar a escolha e o motivo neste `design.md`
- [ ] 4.2 Decidir o tratamento LGPD do DeepSeek (opção a, b ou c) e registrar neste `design.md`
- [ ] 4.3 Atualizar o status no `ROADMAP.md` e arquivar a mudança
