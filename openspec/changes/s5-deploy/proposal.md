# Proposal

## Why

A aplicação nunca foi publicada. O deploy saiu da S2 por decisão de 09/11, com a plataforma em aberto, e a spec `plataforma` exige que, a partir da S5, cada mudança esteja publicada antes de ser arquivada. A `s5-entrada-audio` acrescenta o Whisper ao RAG, e a memória estimada passa a ~3,1 GB, o que exclui os planos gratuitos pequenos. O achado de 09/11 sobre o Hugging Face nunca tinha sido conferido; em 24/11 a documentação oficial confirmou que criar um Space Docker exige o plano PRO.

Métrica do ROADMAP: critério 4 de "pronto" (publicada na URL de teste, a partir da S5). Prepara a medição do **tempo até o 190 (≤ 2 s)** e do **p95 ≤ 10 s** no ambiente publicado, que são da S6. O critério de pronto da S5 ("uma pergunta por áudio respondida de ponta a ponta") não exige a URL publicada (decisão de 24/11).

## What Changes

- **Primeira tarefa (quinta, 26/11):** decidir a plataforma e o uso de Docker com a tabela do design e a memória medida pela `s5-entrada-audio`, registrar o motivo e rodar `/opsx:update`. Até lá, as tarefas de empacotar e publicar ficam genéricas.
- Recebe as pendências de deploy da S2: o `Dockerfile` (ou o empacotamento equivalente), o workflow de CI, a publicação e a decisão da plataforma (`s2-plataforma-base` 3.1, 3.2, 3.3 e 4.1) e a verificação na URL publicada (`s2-rag-juridico` 2.4).
- Requisitos com ou sem Docker: torch só para CPU no Linux, sem quebrar o `uv.lock` nem o ambiente local no Windows; os modelos `multilingual-e5-base` e Whisper baixados no build, sem download ao subir; partida a frio medida (índice de ~20 s mais o Whisper); vetores do índice gerados no build, se couber no dia (senão, S6); chave do DeepSeek só em variável de ambiente da plataforma; uvicorn com `--no-access-log`.
- Só com Docker: `.dockerignore` com `.env`, `.venv`, `.git` e `__pycache__`. O Docker Desktop local ajuda, mas não é obrigatório.
- Se a escolha for sem Docker, o `/opsx:update` altera a spec `plataforma` ("a partir de um único container"), a equipe decide o que muda no `openspec/config.yaml`, e o `Dockerfile` pode ir para a S6.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `plataforma`: modelos locais incluídos na publicação, sem download ao subir; partida a frio medida e registrada; chave do LLM só como segredo do ambiente publicado.
- `privacidade-seguranca`: o servidor publicado roda sem log de acesso.

## Impact

- **Arquivos novos (conforme a decisão de quinta):** `Dockerfile` e `.dockerignore`, ou a configuração de build nativo da plataforma; `.github/workflows/testes.yml`; um script de build que baixa os modelos e, se couber, gera os vetores.
- **Arquivos alterados:** `pyproject.toml` e `uv.lock` (índice de torch para CPU no Linux), `app/rag/indice.py` (vetores prontos, se couber), `README.md` (como publicar), `ROADMAP.md`.
- **Custo e contas:** nenhuma opção que caiba na memória é gratuita sem cartão (tabela no design). A decisão depende de aprovação de gasto e de quem é dono da conta.
- **Privacidade (LGPD):** a plataforma passa a processar as requisições, inclusive o áudio e o texto da usuária, no servidor dela; a escolha registra a região e se a plataforma guarda logs de borda (IP, URL). Nenhum dado é guardado pela aplicação. O DeepSeek segue a opção (c) de 09/11: só casos fictícios. A chave nunca vai para a imagem, o repositório ou os logs de build.
- **Segurança da usuária:** a URL de teste é pública e a aplicação pode "dormir"; o alerta de 190 e a saída rápida funcionam no aparelho, sem esperar o servidor acordar. A partida a frio só atrasa as respostas.
- **Fora desta mudança:** o domínio próprio, o nome e o ícone definitivos e o deploy final (`s6-producao`); a medição no celular do tempo até o 190 e do p95 (`s6-producao`); os vetores no build, se não couberem na quinta (S6); o `Dockerfile`, se a plataforma escolhida for sem Docker (S6); fotos (decisão de 24/11).
