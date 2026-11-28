# Rede Lilás

Apoio a mulheres em situação ou risco de violência doméstica no Distrito Federal: reconhecer violações de direitos, avaliar o risco e encontrar benefícios e serviços de acolhimento. Definições em `docs/`, plano semanal em `ROADMAP.md` e mudanças em `openspec/changes/`.

## Preparar o ambiente

Requisitos: Python 3.12+ e [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest
```

Na primeira execução, o modelo de embeddings `intfloat/multilingual-e5-base` (cerca de 1,1 GB) é baixado do Hugging Face para o cache local. Os embeddings rodam no próprio processo, sem serviço externo.

O GitHub Actions roda a mesma suíte (`uv run pytest`, com Python 3.12) em todo PR para a `develop` ou a `main` (`.github/workflows/testes.yml`). PR em rascunho não roda.

## Rodar o servidor

O LLM é configurado por `LLM_BASE_URL`, `LLM_MODEL` e `LLM_API_KEY`. Nos testes locais usamos o [Ollama](https://ollama.com):

```bash
cp .env.example .env                 # .env não é versionado
ollama pull qwen2.5:7b-instruct
uv run --env-file .env uvicorn app.main:app --reload --no-access-log
curl localhost:8000/saude            # {"status":"ok"}
```

Sempre use `--no-access-log`: o access log do uvicorn grava a query string e o IP de quem acessa. O log da aplicação (`app/logs.py`) registra só método, rota, status, duração e tipo de erro.

Para conferir o LLM sem subir o servidor (só com perguntas fictícias):

```bash
uv run --env-file .env python -m app.llm "O que é violência patrimonial?"
```

`LLM_TIMEOUT` (opcional, padrão 30) é quantos segundos o servidor espera o LLM antes de responder que não consegue agora, sem tentar de novo. Se mudar, ajuste `TEMPO_LIMITE_MS` em `web/app.js` para um pouco acima desse valor: a tela precisa esperar mais que o servidor.

`LLM_THINKING` (opcional) liga ou desliga o raciocínio do modelo: com `disabled` ou `enabled`, a chamada envia esse parâmetro do DeepSeek; sem a variável, nada é enviado, como o Ollama espera.

Para usar o DeepSeek, troque as variáveis no `.env` (veja o bloco comentado em `.env.example`): modelo `deepseek-flash` com `LLM_THINKING=disabled`. Nenhum código muda. A chave fica só no `.env` de cada máquina e nunca é versionada. Pela decisão de LGPD (opção (c), em `openspec/changes/archive/2026-11-24-s2-plataforma-base/design.md`), só casos fictícios vão ao DeepSeek.

## Rodar com Docker

O `Dockerfile` monta a aplicação num único container, o mesmo usado no deploy. A imagem já traz o Whisper, o modelo de embeddings e os vetores do índice, e o container sobe com `HF_HUB_OFFLINE=1`, sem baixar modelos. A imagem tem cerca de 3,6 GB, e o primeiro build leva alguns minutos.

```bash
docker build -t rede-lilas .
docker run --rm -p 8000:8000 --env-file .env rede-lilas
curl localhost:8000/saude            # {"status":"ok"}
```

- A chave do LLM entra só em execução (`--env-file .env` ou variável secreta da plataforma), nunca na imagem. O `.dockerignore` deixa `.env` e `.env.*` fora do build.
- `PORT` (padrão 8000) troca a porta, por exemplo `-e PORT=7860` no Hugging Face Spaces.
- Para usar outro modelo do Whisper, passe o mesmo valor no build: `docker build --build-arg WHISPER_MODELO=base -t rede-lilas .`.
- Antivírus que inspecionam HTTPS, como o Kaspersky, podem fazer o build falhar de vez em quando com `CERTIFICATE_VERIFY_FAILED` ao baixar os modelos. Rodar o build de novo costuma resolver; as camadas já prontas ficam em cache.

## Publicar no Azure

A plataforma é o Azure App Service Linux, plano B3, na região brazilsouth, pago pelo crédito do Azure for Students do Túlio (decisão e medições em `openspec/changes/archive/2026-11-27-s5-deploy/design.md`). Só quem tem acesso a essa assinatura consegue rodar os comandos abaixo.

**Situação em 27/11:** o site e o plano foram apagados para não gastar crédito até a hora de testar de novo (S6 e apresentação). Ficou só o grupo `rede-lilas` com o registro de imagens `redelilas.azurecr.io` (Basic, ~US$ 5/mês), que guarda as versões já publicadas. A URL https://rede-lilas.azurewebsites.net está fora do ar.

**Regras que valem sempre:**

- Uma mudança de configuração por vez. Depois de cada uma, espere "Site started" no log da plataforma (`LogFiles/..._docker.log`, pela API do Kudu) antes da próxima. Em 25/11, duas mudanças seguidas derrubaram o site por ~5 minutos.
- A chave do DeepSeek vem do `.env` local e entra só como configuração do site. Nunca na imagem, no repositório ou num comando salvo.
- Não ligar os logs HTTP, os logs da aplicação nem o Application Insights.
- A assinatura de estudante bloqueia o build na nuvem (`az acr build`): a imagem é montada no Docker local e enviada ao registro.
- No Git Bash do Windows, rode `export MSYS_NO_PATHCONV=1` antes dos comandos que recebem IDs `/subscriptions/...`. No `curl` do Windows com o Kaspersky, use `--ssl-no-revoke`.

### Recriar o site

São ~10 a 15 minutos. Use a tag do commit da `develop` como versão da imagem.

```bash
TAG=$(git rev-parse --short HEAD)

# 1. Imagem: build local e envio ao registro (~2 min cada)
docker build -t redelilas.azurecr.io/rede-lilas:$TAG .
az acr login --name redelilas
docker push redelilas.azurecr.io/rede-lilas:$TAG

# 2. Plano B3 (4 núcleos, 7 GB)
az appservice plan create -g rede-lilas -n rede-lilas-plano --is-linux --sku B3 -l brazilsouth

# 3. Site com a imagem
az webapp create -g rede-lilas -p rede-lilas-plano -n rede-lilas \
  --deployment-container-image-name redelilas.azurecr.io/rede-lilas:$TAG

# 4. O site puxa a imagem com identidade gerenciada, sem senha do registro
PRINCIPAL=$(az webapp identity assign -g rede-lilas -n rede-lilas --query principalId -o tsv)
ACR=$(az acr show -n redelilas --query id -o tsv)
az role assignment create --assignee "$PRINCIPAL" --role AcrPull --scope "$ACR"
az webapp config set -g rede-lilas -n rede-lilas --generic-configurations '{"acrUseManagedIdentityCreds": true}'

# 5. Configurações (a chave vem do .env e não aparece no terminal)
LLM_API_KEY=$(grep '^LLM_API_KEY=' .env | cut -d= -f2-)
az webapp config appsettings set -g rede-lilas -n rede-lilas -o none --settings \
  WEBSITES_PORT=8000 WEBSITES_ENABLE_APP_SERVICE_STORAGE=false \
  LLM_BASE_URL=https://api.deepseek.com LLM_MODEL=deepseek-flash LLM_THINKING=disabled \
  LLM_API_KEY="$LLM_API_KEY"

# 6. Sempre ligado, só HTTPS, sem FTP
az webapp config set -g rede-lilas -n rede-lilas --always-on true --ftps-state Disabled \
  --http20-enabled true --min-tls-version 1.2
az webapp update -g rede-lilas -n rede-lilas --https-only true
```

Se o nome `rede-lilas` tiver sido tomado por outra pessoa enquanto o site estava apagado, use outro nome e avise a equipe, porque a URL muda.

**Conferir:** `/saude` responde, a página abre no celular, a transcrição do caso A1 (`tests/audios/a1.webm`) volta certa e uma pergunta jurídica fictícia volta com o art. 7º citado. Depois de cada publicação, a primeira transcrição leva ~25 s; as seguintes, ~8 s.

### Publicar uma nova versão

Com o site no ar: monte e envie a imagem como no passo 1 e troque a imagem do site.

```bash
az webapp config container set -g rede-lilas -n rede-lilas \
  --container-image-name redelilas.azurecr.io/rede-lilas:$TAG
```

O container antigo continua respondendo até o novo passar no teste de saúde, então o site não sai do ar. Os navegadores recebem a interface nova quando a versão do cache em `web/sw.js` muda.

### Apagar o site para não gastar crédito

O B3 custa ~US$ 1,60 por dia, com o site ligado ou parado. A cobrança só para quando o plano é apagado (ou rebaixado para o F1, que não roda a aplicação).

```bash
az webapp delete -g rede-lilas -n rede-lilas   # apaga também o plano, se for o último site nele
```

A atribuição AcrPull da identidade apagada fica sobrando no registro; remova-a com `az role assignment list --scope "$ACR"` e `az role assignment delete --ids <id>`. O registro e as imagens continuam.

## Pergunta por áudio

O botão de microfone da conversa grava até 30 s, só na memória da aba, e envia o áudio a `POST /transcrever`, no próprio servidor. O servidor transcreve com o Whisper ([faster-whisper](https://github.com/SYSTRAN/faster-whisper), modelo `small` em int8 na CPU, português fixo) e devolve só o texto. O áudio nunca vai a serviço externo, não é gravado em disco e não aparece nos logs. A regra de risco roda no navegador sobre o texto: com sinal de risco, o 190 aparece na hora; sem risco, o texto vai para a caixa, para conferir e enviar.

- O servidor carrega o Whisper ao subir, em segundo plano. Na primeira vez em cada máquina, ele baixa o modelo, cerca de 0,5 GB. Até a carga terminar, a rota responde que a transcrição está iniciando.
- `WHISPER_MODELO` (opcional, padrão `small`) troca o modelo; `base` é a reserva, mais rápida e menos precisa. `WHISPER_THREADS` (opcional) limita as threads, por exemplo `2` para medir como numa máquina de 2 vCPUs.
- A telemetria do onnxruntime (usado pelo filtro de silêncio) fica desligada pelo próprio código (`ORT_DISABLE_TELEMETRY=1`).

Os casos fictícios de áudio (A1 a A7, voz sintética) estão em `tests/audios/`. O `LEIAME.md` dessa pasta explica como gerá-los de novo ou trocar por uma gravação da equipe. Os testes que usam o Whisper de verdade ficam fora do `uv run pytest` e rodam com:

```bash
uv run pytest -m whisper
```

## Layout no celular

Os testes que medem o layout num navegador de verdade (saída rápida inteira no cabeçalho e chat dentro da tela, de 320 a 430 px de largura) também ficam fora do `uv run pytest`. Eles precisam do Chromium do Playwright, instalado uma vez por máquina:

```bash
uv run playwright install chromium
uv run pytest -m navegador
```

## Base jurídica (RAG)

18 normas federais e distritais, listadas em `dados/fontes/fontes.yaml`, cada uma com um eixo: `juridico`, `beneficios`, `saude` ou `df`.

| Pasta | Conteúdo |
|---|---|
| `dados/fontes/raw/` | HTML original de cada coleta, guardado byte a byte |
| `dados/fontes/dispositivos/` | dispositivos extraídos (`.jsonl`), por norma e data da coleta |
| `dados/fontes/relatorios/` | relatório de alterações de cada coleta |
| `dados/leis/` | trechos que alimentam o índice, um arquivo por norma |

Tudo é versionado. O índice é montado em memória a partir de `dados/leis/` quando a aplicação inicia, o que leva cerca de 30 s na CPU. Para subir mais rápido (no deploy, por exemplo), gere antes os vetores dos trechos:

```bash
uv run python -m app.rag.indice   # grava dados/indice/vetores.npz (fora do git)
```

Com o arquivo presente, o índice carrega em menos de 1 s. Os vetores só são usados se os trechos de `dados/leis/` e o modelo forem os mesmos de quando o arquivo foi gerado; senão, o índice é montado na hora, como sem o arquivo. A aplicação nunca grava esse arquivo: ele é gerado só pelo comando acima.

### Consultar

```bash
uv run python -m app.rag.buscar "ele quebrou minhas coisas, isso é violência?"
uv run python -m app.rag.buscar "tenho direito a auxílio-aluguel?" --eixo df --eixo beneficios -k 3
```

O número entre colchetes é a similaridade de cosseno (quanto maior, mais parecido). A orientação jurídica busca só no eixo `juridico`.

### Atualizar as normas

```bash
uv run python -m app.rag.coleta                      # baixa todas as normas de fontes.yaml
uv run python -m app.rag.coleta --norma <id> --norma <id>            # só essas normas, num relatório
uv run python -m app.rag.coleta --norma <id> --arquivo pagina.html   # usa um HTML já baixado
uv run python -m app.rag.coleta --reprocessar        # relê o HTML salvo com o leitor atual, sem baixar
uv run python -m app.rag.ingestao                    # gera os trechos em dados/leis/
uv run pytest
```

A coleta não altera os trechos: revise `dados/fontes/relatorios/<data>.md` antes de rodar a ingestão. Para incluir uma norma, adicione-a a `fontes.yaml` (com `eixo`) e rode a coleta e a ingestão.
