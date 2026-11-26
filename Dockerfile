# Rede Lilás em um único container (s5-deploy, tarefa 2.2; vem de s2-plataforma-base 3.1).
# Serve aos dois planos de deploy: Azure App Service (plano A) e Hugging Face Spaces (plano B).
#
#   docker build -t rede-lilas .
#   docker run --rm -p 8000:8000 --env-file .env rede-lilas
#
# Os modelos (embeddings e Whisper) e os vetores do índice ficam prontos na imagem, e o container
# sobe com HF_HUB_OFFLINE=1: nenhum download de modelo em execução. A chave do LLM nunca entra na
# imagem; vem só por variável de ambiente da plataforma.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.10 /uv /uvx /bin/

# Usuário sem privilégios com UID 1000, que o Hugging Face Spaces exige.
RUN useradd --create-home --uid 1000 user
USER user
WORKDIR /home/user/app

# Modelo do Whisper baixado no build. Trocar em execução (WHISPER_MODELO) pede outro build com o
# mesmo valor, porque o container não baixa modelos: docker build --build-arg WHISPER_MODELO=base .
ARG WHISPER_MODELO=small
# UV_NO_CACHE: sem ele, o cache de download do uv (~1,5 GB) ficaria dentro da imagem.
ENV UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    HF_HOME=/home/user/.cache/huggingface \
    PATH="/home/user/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    WHISPER_MODELO=$WHISPER_MODELO

# Dependências antes do código: mudar o código não refaz esta camada. No Linux, o torch vem do
# índice só de CPU (tool.uv.sources no pyproject.toml).
COPY --chown=user pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# Só o que a aplicação lê em execução.
COPY --chown=user app ./app
COPY --chown=user web ./web
COPY --chown=user regras ./regras
COPY --chown=user dados/leis ./dados/leis
COPY --chown=user dados/rede_protecao_df.csv dados/cep_ra_df.csv ./dados/

# Baixa o Whisper e o multilingual-e5-base e grava os vetores do índice (dados/indice/vetores.npz).
RUN python -c "import os; from faster_whisper import WhisperModel; WhisperModel(os.environ['WHISPER_MODELO'], device='cpu', compute_type='int8')" \
 && python -m app.rag.indice

ENV HF_HUB_OFFLINE=1 \
    PORT=8000
EXPOSE 8000

# --no-access-log: o access log do uvicorn grava a query string e o IP (design da s2-plataforma-base).
# A porta vem de PORT: 8000 por padrão; a plataforma pode trocar (o HF Spaces usa 7860).
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port \"$PORT\" --no-access-log"]
