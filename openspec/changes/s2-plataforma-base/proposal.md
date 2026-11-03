# Proposal

## Why

Sem um esqueleto comum, as outras mudanças da S2 (alerta 190 e RAG jurídico) não têm onde rodar, e o deploy acaba ficando para a S6, quando já não haverá tempo para resolver problemas de memória, configuração ou provedor. Esta mudança cria a base técnica e publica a aplicação ainda na S2.

Métricas do ROADMAP afetadas: tempo até o 190 (≤ 2 s) e tempo de resposta (p95 ≤ 10 s), que só podem ser medidos com a aplicação publicada.

## What Changes

- Backend FastAPI (gerenciado com `uv`, testado com `pytest`) que também serve a PWA.
- PWA mínima em HTML/CSS/JS puros: tela de conversa, manifest, service worker, botão de saída rápida, conversa só em memória e nome/ícone provisórios discretos.
- Cliente de LLM único, compatível com a API da OpenAI (Ollama local ou DeepSeek), configurado por `LLM_BASE_URL`, `LLM_MODEL` e `LLM_API_KEY`.
- Logs só com dados técnicos (sem texto das mensagens).
- `Dockerfile`, `.env.example`, `.gitignore` e workflow de CI com `pytest`.
- Primeiro deploy em uma URL de teste.
- Registro das duas decisões da S2: plataforma de deploy e tratamento LGPD do DeepSeek.

Requisitos implementados (specs da base): `plataforma` (Provedor de LLM configurável; Segredos fora do repositório; Implantação contínua; Decisão de privacidade do provedor registrada), `privacidade-seguranca` (Saída rápida; Sem histórico persistente; Dados pessoais fora dos logs; Aparência discreta) e `interface-pwa` (Instalável).

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

Nenhuma. A mudança implementa requisitos já definidos em `s1-definicoes-base`.

## Impact

- Cria a estrutura de código do repositório (`app/`, `web/`, `tests/`, `regras/`, `dados/`).
- **Privacidade (LGPD):** nenhum dado da usuária é armazenado no servidor; os logs não guardam conteúdo. O envio ao DeepSeek fica bloqueado até a decisão registrada (sexta, 06/11).
- **Segurança da usuária:** saída rápida e ausência de histórico já disponíveis na primeira versão publicada.
- **Fora desta mudança:** perfil local (S3), perguntas sugeridas (S4), ícone e nome definitivos (S6) e auditoria WCAG completa (S6).
