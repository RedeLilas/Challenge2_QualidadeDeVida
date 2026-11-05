# Design

## Context

O repositório ainda não tem código. A equipe trabalha 3 dias por semana, e restam 2 dias na S2 (quinta, 05/11, e sexta, 06/11). Requisitos que pesam no desenho: o modelo de embeddings roda localmente (o DeepSeek não oferece embeddings), a S5 deve incluir transcrição de áudio (Whisper) e a PWA precisa funcionar em celular básico e conexão lenta.

## Goals / Non-Goals

**Goals:**
- Uma unidade de deploy (um container) com backend e PWA.
- Troca entre LLM local e de produção apenas por variáveis de ambiente.
- URL de teste publicada até sexta, 06/11.

**Non-Goals:**
- Frameworks de frontend (React, Vue) e etapa de build no frontend.
- Banco de dados (não há dados de usuária no servidor).
- Autenticação (não há contas).

## Decisions

### Estrutura do repositório

```
app/            # backend FastAPI
  main.py       # rotas e montagem da PWA estática
  config.py     # leitura de variáveis de ambiente
  llm.py        # cliente único de LLM
  logs.py       # middleware de log sem conteúdo
web/            # PWA: index.html, app.js, styles.css, manifest.webmanifest, sw.js
regras/         # regras versionadas (ex.: risco_imediato.json)
dados/          # fontes curadas e índices
tests/
Dockerfile
.env.example
```

### Backend: FastAPI servindo a PWA
FastAPI é leve, assíncrono e tem testes simples com `TestClient`. Servir a PWA pelo mesmo processo evita CORS e reduz o deploy a um container. Alternativa descartada: frontend separado em Vercel/Netlify, que exigiria dois deploys e configuração de CORS.

### PWA em HTML/CSS/JS puros
Não exige build, é leve para celular básico e qualquer pessoa da equipe consegue editar. O service worker guarda em cache a interface e `regras/risco_imediato.json`, para que o alerta de 190 funcione offline.

### Cliente de LLM compatível com OpenAI
O Ollama expõe `http://localhost:11434/v1` e o DeepSeek expõe `https://api.deepseek.com`, ambos no protocolo da OpenAI. Um único cliente (pacote `openai`) recebe `LLM_BASE_URL`, `LLM_MODEL` e `LLM_API_KEY`. Modelo local para testes: `qwen2.5:7b-instruct` (confirmado em 05/11; responde em 2–3 s na máquina da equipe). O `gemma4:12b-it-qat` foi testado e descartado: gasta cerca de 30 s raciocinando antes de responder e estoura o tempo limite da rota.

### Saída rápida
Botão fixo em todas as telas. Ao tocar: limpa o estado da conversa em memória e chama `location.replace()` para um site neutro (ex.: previsão do tempo). O `replace` não deixa a página no histórico do navegador. A conversa nunca vai para `localStorage`.

### Logs sem conteúdo
Middleware registra método, rota, status e duração. Exceções são registradas com tipo e rota, sem o corpo da requisição.

O uvicorn MUST rodar com `--no-access-log` (inclusive no `Dockerfile`): o access log padrão grava a query string e o IP de quem acessa, e o middleware já cobre o que é necessário. Texto da usuária vai sempre no corpo da requisição, nunca na URL.

### Pendente até sexta, 06/11: plataforma de deploy

| Critério | Hugging Face Spaces (Docker) | Render (free) | VPS (ex.: Oracle Free, Hetzner) |
| :--- | :--- | :--- | :--- |
| Memória para embeddings e, na S5, Whisper | Ampla no plano gratuito de CPU | Muito limitada | Depende do plano |
| Esforço de configuração | Baixo (push do repositório) | Baixo | Alto (servidor, HTTPS, atualizações) |
| Inatividade | "Dorme" sem uso; acorda no acesso | "Dorme" sem uso | Sempre ligado |
| Visibilidade | Space público | Privado possível | Privado |

**Recomendação:** Hugging Face Spaces com Docker, desde que a equipe confirme os limites atuais do plano gratuito. O `Dockerfile` mantém a aplicação portátil caso seja preciso migrar.

### Pendente até sexta, 06/11: DeepSeek e LGPD
A API oficial do DeepSeek processa dados fora do Brasil (transferência internacional, LGPD art. 33), e as mensagens podem conter relatos de violência. Opções:

- **(a)** API oficial com anonimização antes do envio (remover nomes, telefones, endereços e números de documento).
- **(b)** Pesos abertos do DeepSeek servidos por outro provedor, com política de dados conhecida.
- **(c)** API oficial com o risco declarado no relatório, usada só com casos fictícios durante o projeto.

Enquanto não houver decisão, o ambiente publicado usa o LLM local ou chamadas apenas com casos fictícios. A avaliação da S3 não é bloqueada, porque usa só casos fictícios.

## Risks / Trade-offs

- **Space público e "dormindo"**: a primeira resposta após a inatividade é lenta e pode distorcer a medição de latência. Mitigação: medir a latência com a aplicação já acordada e registrar o tempo de acordar à parte.
- **LLM local fraco em português**: as respostas nos testes podem ser piores que em produção. Mitigação: as métricas oficiais são medidas com o modelo de produção.
- **JS sem testes automatizados**: a PWA não tem suíte de testes nesta mudança. Mitigação: verificação manual da saída rápida e do alerta com roteiro fixo.
