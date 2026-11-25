# Design

## Context

- A aplicação é um processo FastAPI servindo a PWA (`app/main.py`), com o índice do RAG montado em memória ao subir (`app/rag/indice.py`: `multilingual-e5-base` sobre `dados/leis/*.jsonl`, cerca de 20 s numa máquina de 28 núcleos lógicos, pico de 2,5 GB medido em 09/11) e, com a `s5-entrada-audio`, o Whisper `small` em int8 (estimativa: ~0,6 GB a mais). Estimativa total: ~3,1 GB, a confirmar pela tarefa 5.1 da `s5-entrada-audio`.
- O `uv.lock` resolve o torch 2.15.0 pelo PyPI. No Linux, o torch do PyPI traz as bibliotecas de CUDA (alguns GB), inúteis num servidor só com CPU. No Windows e no macOS, o torch do PyPI já é só CPU.
- O design da `s2-plataforma-base` (arquivado em `openspec/changes/archive/2026-11-24-s2-plataforma-base/design.md`) já exige uvicorn com `--no-access-log`, segredos só em variáveis de ambiente e uma única unidade de deploy.
- A equipe tem só a quinta (26/11) para esta mudança. A plataforma e o uso de Docker são decididos na quinta, como primeira tarefa (decisão de 24/11).

## Goals / Non-Goals

**Goals:**
- Decidir a plataforma e o uso de Docker com dados conferidos e a memória medida.
- Publicar a aplicação com os modelos no build, sem chave no pacote e sem log de acesso.
- Medir a partida a frio e verificar na URL publicada a pergunta da persona Camila (art. 7º) e uma pergunta por áudio.

**Non-Goals:**
- Domínio próprio, nome e ícone definitivos, deploy final e medição de latência no celular (`s6-producao`).
- Escalar para mais de uma instância.

## Decisions

### Plataforma: tabela para a decisão de quinta (conferida na web em 24/11)

Orçamento de memória: ~3,1 GB estimados → é preciso uma instância de **4 GB ou mais**.

| Plataforma | Memória disponível | Docker ou Python nativo | Custo e cartão | Dorme? | Esforço para publicar |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Hugging Face Spaces, CPU Basic** | 16 GB, 2 vCPU, 50 GB de disco não persistente | Docker (SDK `docker`) | Hardware grátis, mas **criar Space Docker exige o PRO (US$ 9/mês)** numa conta pessoal, ou Team (US$ 20/usuário/mês) numa organização. Cartão: sim | Sim, depois de 48 h sem uso; acorda no acesso | Baixo: `git push` com `Dockerfile` (porta 7860) |
| Hugging Face Spaces sem plano pago | Só Spaces estáticos ou Gradio com ZeroGPU | Não roda o FastAPI | Grátis | — | Não serve |
| Render | Grátis: 512 MB e 0,1 CPU (não cabe). Pagos: 1 CPU/2 GB (`standard`, não cabe), 2 CPU/4 GB (`pro`) | Docker ou Python nativo | Preço do `pro` não apareceu na página oficial (lida em 24/11); sites de terceiros dão ~US$ 85/mês. Cartão: sim nos pagos | Grátis dorme depois de 15 min (acorda em ~1 min); pagos não dormem | Baixo |
| Railway | Free: 0,5 GB. Trial: 1 GB (não cabem). Hobby: até 48 GB por serviço | Docker ou Python nativo (build automático) | Hobby US$ 5/mês com US$ 5 de uso incluído; RAM a US$ 10/GB/mês e CPU a US$ 20/vCPU/mês. Ligado o mês todo com ~3,5 GB: ~US$ 35 a 45/mês (nossa conta). Cartão: sim (pós-pago) | Não por padrão (há opção de dormir sem uso) | Baixo |
| Fly.io | Máquinas sob medida; 4 GB não é um preset | Docker (gera o `Dockerfile` para Python) | `shared-cpu-2x` com 2 GB: US$ 13,39/mês; RAM extra a US$ 6/GB/mês → 4 GB ≈ US$ 25/mês (nossa conta). Cartão: sim | Opcional (auto stop/start); parada, paga só o disco | Médio: `flyctl` e `fly.toml` |
| Google Cloud Run | Configurável por instância (até 32 GiB) | Imagem Docker, ou código-fonte com buildpacks | Cota grátis mensal de 360 mil GiB-s (uma instância de 4 GiB ligada sem parar gasta a cota em ~25 h); escala a zero. Cartão: sim (conta de faturamento) | Sim, escala a zero; cada acordar paga a carga do índice e do Whisper | Médio: `gcloud`, registro de imagens |
| VPS (ex.: Oracle Cloud Always Free, Hetzner) | Depende do plano | Qualquer um | Não verificado em 24/11. Cartão: sim | Não | Alto: servidor, HTTPS, atualizações e segurança por conta da equipe |
| Koyeb | Não conferido: a página oficial (24/11) não mostrou instância gratuita de CPU nem preço de CPU com 4 GB | Docker ou nativo | Não conferido | — | — |
| **Azure App Service Linux, plano B3** (acrescentado em 24/11, #120) | 7 GB, 4 núcleos (B2: 3,5 GB, apertado para o pico de ~2,9 GB) | Docker (container próprio) ou Python nativo | ~US$ 50/mês, estimativa a conferir na calculadora logada na conta de estudante. Pago pelo **Azure for Students**: US$ 100 de crédito, sem cartão, válido por 12 meses; quando o crédito acaba, os serviços param, sem cobrança. Cartão: não | Não, com o Always On ligado | Médio: `az` CLI ou portal; HTTPS incluído |
| Azure Container Apps (acrescentado em 24/11) | Configurável por réplica | Docker | Cobrança por segundo, com cota grátis mensal de 180 mil vCPU-s e 360 mil GiB-s; também pago pelo crédito de estudante | Sim, escala a zero; cada acordar paga a carga do índice e do Whisper, como no Cloud Run | Médio |

Fontes (consultadas em 24/11; as páginas do HF, do Render, do Railway e do Koyeb foram lidas, e as da Fly.io e do Cloud Run, por busca): [HF Spaces overview](https://huggingface.co/docs/hub/spaces-overview), [HF Docker Spaces](https://huggingface.co/docs/hub/spaces-sdks-docker), [HF hardware](https://huggingface.co/docs/hub/en/spaces-gpus), [HF pricing](https://huggingface.co/pricing), [Render compute plans](https://render.com/docs/compute-plans), [Render free](https://render.com/docs/free), [Railway plans](https://docs.railway.com/reference/pricing/plans), [Fly.io pricing](https://docs.fly.io/about/pricing), [Cloud Run pricing](https://cloud.google.com/run/pricing), [Koyeb pricing](https://www.koyeb.com/pricing). Azure, por busca em 24/11 (as páginas de preço só mostram valores com login, então os preços do Azure acima são estimativas): [Azure for Students](https://azure.microsoft.com/en-us/free/students/), [oferta MS-AZR-0170P](https://azure.microsoft.com/en-us/pricing/offers/ms-azr-0170p/), [App Service no Linux](https://azure.microsoft.com/en-us/pricing/details/app-service/linux/), [cobrança do Container Apps](https://learn.microsoft.com/azure/container-apps/billing).

**Achado de 09/11 conferido em 24/11:** confirmado. A documentação oficial diz que "Gradio and Docker Spaces run on compute and require a paid plan to create: PRO for personal accounts, Team or Enterprise for organizations". O CPU Basic continua com 2 vCPU, 16 GB e "Free!" por hora, e dorme depois de 48 h sem uso. A recomendação da S2 (HF Spaces grátis) não vale mais sem o PRO.

**Leitura para quinta (recomendação preliminar, não é a decisão):** o HF Spaces com PRO é a opção mais barata que cabe com folga (US$ 9/mês, 16 GB) e tem o menor esforço, mas exige Docker e a conta PRO de uma pessoa da equipe (ou Team na organização). A Fly.io (~US$ 25/mês) e o Railway (~US$ 35 a 45/mês) são as reservas com Docker ou nativo. O Cloud Run sai quase de graça com pouco uso, mas cada acordar paga a carga do índice e do Whisper, o que atrapalha a medição da S6. O Render só cabe no plano de 4 GB, o mais caro da tabela.

**Orientação da equipe (24/11, #120; não é a decisão, que fica para a tarefa 1.1 e pode mudar se aparecer alternativa melhor):**

- **Plano A: Azure App Service Linux B3**, pago pelo crédito do Azure for Students do Túlio. Cabe com folga, não dorme, não exige cartão e não custa nada à equipe até o fim da S7. A região Brazil South pode ajudar na questão de LGPD.
- **Plano B: Hugging Face Spaces com PRO** (US$ 9/mês). Se for preciso, a equipe decide na hora quem assina e como divide o custo.
- **Empacotar com Docker:** o HF só aceita Docker, e o App Service roda container. Com o mesmo `Dockerfile` para os dois, trocar de plano vira só publicar em outro lugar.
- **Quando trocar:** se até o meio da quinta o Azure não estiver respondendo em `/saude`, a equipe passa para o plano B.

### Decisão (24/11, tarefa 1.1)

Registrada em 24/11, antes de quinta, depois do teste no Azure e do container verificado na tarefa 2.2. Pode ser revista se aparecer alternativa melhor: um novo `/opsx:update` registra a troca e o motivo.

- **Plataforma:** Azure App Service Linux, plano **B3** (4 núcleos, 7 GB), região **brazilsouth** (São Paulo), na assinatura Azure for Students do Túlio.
- **Empacotamento:** Docker, com o `Dockerfile` da tarefa 2.2. A mesma imagem serve ao plano B. A spec `plataforma` não muda: ela já pede um único container.
- **Motivo:**
  - cabe com folga: pico medido de ~2,9 GB (tabela abaixo) e 1,4 GB em uso no container local em 24/11, contra 7 GB do B3;
  - não dorme, com o Always On ligado;
  - nenhum gasto da equipe e nenhum cartão, porque o crédito do Azure for Students cobre até o fim da S7;
  - servidor no Brasil;
  - testado em 24/11: um plano B3 Linux foi criado e apagado com sucesso em brazilsouth.
- **Regiões permitidas pela assinatura de estudante:** brazilsouth, northcentralus, spaincentral, southafricanorth e belgiumcentral. A reserva é a northcentralus; a eastus não é permitida.
- **Onde guardar a imagem:** escolhido na tarefa 3.1, entre o Azure Container Registry Basic (pago pelo crédito) e o GitHub Container Registry. O repositório já é público, e a imagem não tem segredos. **Escolhido o Azure Container Registry Basic (seção "Publicação (24/11, tarefa 3.1)").**
- **Logs de borda:** não ligar coleta de logs HTTP nem o Application Insights. O log do container só tem o que a aplicação escreve (método, rota, status e duração). A tarefa 3.1 confere o que o App Service guarda por padrão. Registros internos da Microsoft, fora do controle da equipe, entram no relatório como limitação.
- **Plano B mantido:** Hugging Face Spaces com PRO, com a mesma imagem e `PORT=7860`, se até o meio da quinta o Azure não estiver respondendo em `/saude`.

### Publicação (24/11, tarefa 3.1)

**URL de teste:** https://rede-lilas.azurewebsites.net, publicada pelo Túlio em 24/11 com a imagem do commit `4b7b513`.

- **Recursos** (grupo `rede-lilas`, região brazilsouth, assinatura Azure for Students do Túlio):
  - **Registro:** Azure Container Registry Basic `redelilas.azurecr.io`, privado e sem usuário administrador. Escolhido no lugar do GitHub Container Registry para o site puxar a imagem por identidade gerenciada, sem senha nem token guardado, e para a imagem ficar na mesma região.
  - **Plano:** `rede-lilas-plano`, App Service Linux B3.
  - **Site:** `rede-lilas`, com identidade gerenciada do sistema e papel AcrPull no registro; Always On ligado; só HTTPS (o `http://` redireciona com 301), TLS mínimo 1.2, HTTP/2 e FTP desligado.
  - **Configurações do site:** `WEBSITES_PORT=8000`, `WEBSITES_ENABLE_APP_SERVICE_STORAGE=false`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_THINKING` e `LLM_API_KEY`. A chave do DeepSeek existe só nessa configuração e no `.env` local; não está na imagem nem no repositório, e o `.dockerignore` deixa o `.env` fora do build.
- **Como publicar uma nova versão:** a assinatura de estudante bloqueia o build na nuvem do registro (`az acr build` devolve `TasksOperationsNotAllowed`). O caminho é `docker build` local com a tag do commit, `az acr login --name redelilas`, `docker push` e `az webapp config container set` com a nova tag. O envio da imagem de ~3,6 GB levou 2 min 26 s. No Git Bash do Windows, exportar `MSYS_NO_PATHCONV=1` antes de comandos `az` que recebem IDs `/subscriptions/...`.
- **O que o App Service guarda de log por padrão** (conferido em 24/11 na pasta `LogFiles` do site, pela API do Kudu): a coleta de logs HTTP, de erros detalhados, de requisições com falha e da aplicação ficou desligada, e o Application Insights não foi criado. O único arquivo é o log da plataforma (`..._docker.log`, 92 linhas), com o download da imagem, a partida do container e os testes de saúde da própria plataforma. Ele não tem query string, chave, texto de pergunta ou de áudio, nem IP. Os registros internos da Microsoft na borda (balanceador e front-end do App Service) ficam fora do controle da equipe e entram no relatório como limitação.
- **Verificação (24/11):**

| Verificação | Resultado |
| :--- | :--- |
| `/saude` e página inicial | Respondem; a PWA carrega (32 KB) |
| Transcrição do caso A1 | "Ele pode tirar meus filhos de mim?", em 7,3 s |
| Pergunta jurídica fictícia | Respondida com a Lei 11.340/2006, art. 7º, citada, em 3,8 s |
| Requisição com query string fictícia | Nada dela nos logs |
| Celular | A URL abriu a PWA no celular do Túlio |

### Partida a frio e memória no Azure (25/11, tarefa 3.2)

**Ambiente:** Azure App Service Linux B3 (4 núcleos, 7 GB), brazilsouth, imagem `4b7b513`. **Como:** site parado até sair do ar e ligado de novo (`az webapp stop` e `start`), com um script consultando a URL a cada segundo: `/saude`, um `POST /transcrever` vazio (503 enquanto o Whisper carrega, 422 quando está pronto, sem enviar áudio) e uma pergunta jurídica fictícia disparada assim que `/saude` respondeu. Os tempos da plataforma vêm do log `..._docker.log`, e a memória, da métrica `MemoryWorkingSet` do Azure Monitor (média por minuto).

| Etapa | Tempo |
| :--- | :--- |
| Plataforma começa a subir → container iniciado | ~10 s (imagem já no servidor; o primeiro download, na publicação, levou 59 s) |
| Container iniciado → `/saude` respondendo | 6,1 s (igual nas 3 partidas medidas) |
| `/saude` → Whisper pronto | 7,7 s |
| `/saude` → primeira pergunta jurídica respondida | 35,0 s, dos quais ~3 s são do DeepSeek: o índice fica pronto ~32 s depois de `/saude` |
| Pergunta jurídica com tudo carregado | 2,7 a 3,6 s |
| Transcrição do caso A1 com tudo carregado | 8,0 s |

- **Total da partida a frio**, da plataforma começando a subir até tudo pronto: ~16 s até `/saude`, ~24 s até o Whisper e ~48 s até o índice. Com o Always On, isso só acontece numa nova publicação ou num reinício.
- **Reinício (`az webapp restart`) não derruba o site:** o container antigo segue respondendo até o novo passar no teste de saúde da plataforma.
- **Índice:** a mesma imagem, no Windows com o Docker limitado a 4 núcleos, carrega o índice do arquivo de vetores em 6,3 s (1,5 s de import do torch e 4,8 s do modelo e dos vetores). No Azure, levou ~32 s. O uso de CPU no minuto da partida (40 s de CPU) é menor do que o recálculo dos vetores pediria, o que indica carga do arquivo com leitura lenta do disco na primeira vez e o Whisper carregando ao mesmo tempo. A aplicação não registra a origem do índice, então isso não está confirmado.
- **Memória em uso:** 1.377 MB com o RAG e o Whisper carregados, depois de uma transcrição, e 1.591 MB depois da rodada de testes da tarefa 3.1. Menos de um quarto dos 7 GB do B3, dentro do pico de ~2,9 GB medido no Mac.

### O que precisa estar pronto antes da decisão de quinta

Respondido em 24/11 na #120.

- [x] Memória e tempos medidos (tarefa 5.1 da `s5-entrada-audio`), na tabela abaixo: pico de ~2,9 GB (24/11).
- [x] Aprovação de gasto: quanto por mês e até quando (a S7 termina em 11/12), e quem aprova. **No plano A, nenhum gasto da equipe: o crédito do Azure for Students cobre até o fim da S7.**
- [x] Dono da conta e do cartão: conta pessoal (HF PRO, Fly.io) ou da organização `RedeLilas` (HF Team, Railway com time). **A equipe. A assinatura do Azure for Students é pessoal e fica no nome do Túlio, para uso da equipe; no plano B, a equipe decide na hora quem assina.**
- [x] Acessos: quem da equipe entra na plataforma e quem vê os segredos. **O Túlio tem o acesso à plataforma e aos segredos e faz a publicação; com a URL no ar, as outras pessoas fazem os testes.**
- [x] Chave do DeepSeek para o ambiente publicado: de quem é, com limite de gasto, e só casos fictícios (opção (c) de 09/11). **Chave do Túlio, com limite de US$ 2 por enquanto (saldo pré-pago).**
- [x] Permissões no GitHub da organização para o workflow de CI e, se a plataforma pedir, para a integração de deploy.
- [x] Créditos de estudante (ex.: GitHub Student Developer Pack, Azure for Students), se alguém da equipe tiver. **O Túlio tem o Azure for Students (US$ 100, sem cartão, 12 meses).**
- [x] Docker Desktop em ao menos uma máquina (ajuda a testar a imagem, mas não é obrigatório).

### Memória e tempos medidos (tarefa 5.1 da `s5-entrada-audio`, 24/11)

**Máquina:** MacBook Air, Apple M4 (4 núcleos de desempenho e 6 de eficiência), 24 GB, macOS 27.0. **Comando:** `uv run python scripts/medir_audio_rag.py`, com cada configuração num processo próprio, embeddings na CPU (como no deploy, sem a GPU do Mac), Whisper `small` em int8 e `HF_HUB_OFFLINE=1`. O script fica no repositório para repetir a medição na plataforma escolhida.

| Medida | Todas as threads (10) | 2 threads |
| :--- | :--- | :--- |
| **Pico de memória com o RAG e o Whisper carregados juntos** | **2.906 MB** | **2.896 MB** |
| Memória ao iniciar o Python com torch (antes dos modelos) | ~905 MB | ~905 MB |
| Carga do Whisper `small` (modelo já no cache) | 0,4 s | 0,4 s |
| Carga do índice (montagem dos vetores de 578 trechos) | 13,6 s | 14,9 s |
| Transcrição de A1 a A6 (média / máximo) | 0,81 / 0,86 s | 1,65 / 1,68 s |
| Pergunta longa, A1 a A6 em sequência (~21 s de fala) | 1,6 s | 2,4 s |
| **A mesma pergunta com ruído forte (SNR -5 dB)** | **10,4 s** | **17,4 s** |
| Busca no RAG | 0,01 s | 0,01 s |

**Leitura para a decisão de quinta:**
- **Memória:** o pico fica em ~2,9 GB, abaixo da estimativa de 3,1 GB. Uma instância de **4 GB cabe**, com cerca de 1 GB de folga para o servidor e os pedidos. Os planos de 0,5 a 2 GB não cabem (Render `free`/`standard`, Railway Free/Trial). O HF Spaces CPU Basic (16 GB) sobra.
- **Tempo:** 2 threads de um M4 são mais rápidas que 2 vCPUs típicas de nuvem. Os tempos acima são um piso e precisam ser medidos de novo na plataforma escolhida, com o mesmo script. A pergunta longa sem ruído (2,4 s em 2 threads) deixa margem para a meta de p95 ≤ 10 s.
- **Áudio com ruído forte:** o faster-whisper refaz a transcrição com outras "temperaturas" quando o resultado parece ruim. Isso multiplica o tempo (17,4 s em 2 threads, e pode passar de 30 s numa nuvem de 2 vCPUs) e não salva o texto. Nesse áudio, com ou sem as novas tentativas, a transcrição sai errada, e a usuária a vê na caixa antes de enviar. Com `temperature=0`, sem novas tentativas, o mesmo áudio levou 1,6 s (10 threads) e 2,4 s (2 threads). Isso provavelmente explica a transcrição de 18 s vista no iPhone em 24/11. A mudança ainda não foi feita: é uma decisão de design da `s5-entrada-audio`.
- **Pergunta repetida:** um áudio com a mesma frase repetida várias vezes sai com a frase uma vez só (o Whisper descarta texto repetitivo). Uma pergunta longa com frases diferentes sai inteira (50 palavras em 21 s).
- **Partida a frio:** carga do índice ~15 s mais Whisper ~0,4 s nesta máquina. Numa nuvem de 2 vCPUs, deve ser bem maior, o que reforça gerar os vetores no build (tarefa 2.3).

### Requisitos com ou sem Docker

- **Torch só para CPU no Linux:** índice `pytorch-cpu` (`https://download.pytorch.org/whl/cpu`) declarado em `[[tool.uv.index]]` com `explicit = true`, e `[tool.uv.sources]` apontando o torch para ele só com o marcador `sys_platform == 'linux'`. No Windows e no macOS o torch continua vindo do PyPI, então o ambiente local não muda. Alternativa descartada: trocar o torch para CPU em todas as plataformas, o que muda o lock de todo mundo sem ganho fora do Linux.
- **Modelos no build:** um script baixa `intfloat/multilingual-e5-base` e o Whisper (`Systran/faster-whisper-small`, ou o modelo de `WHISPER_MODELO`) para o cache do Hugging Face dentro do pacote, e a aplicação sobe com `HF_HUB_OFFLINE=1`. Assim, subir não depende do Hugging Face e não faz chamada externa.
- **Partida a frio:** medida do início do processo até `/saude` e até o índice e o Whisper ficarem prontos. Em 2 vCPU, a montagem dos vetores deve levar bem mais que os ~20 s da máquina de 28 núcleos.
- **Vetores no build, se couber no dia:** o build gera a matriz de vetores (`numpy.save`) junto com um resumo dos trechos (`dados/leis/*.jsonl`) e do modelo; ao subir, o índice carrega a matriz se o resumo bater e só recalcula se não bater. Isso tira a montagem da partida a frio e deve baixar o pico de memória. Se não couber na quinta, vai para a `s6-producao`.
- **Chave do DeepSeek:** só como variável secreta da plataforma (`LLM_API_KEY`), nunca em `ARG`/`ENV` do build nem em arquivo copiado. O `.env` fica fora do pacote.
- **Servidor:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-access-log`, um único processo (os modelos ficam em memória uma vez só).
- **Só com Docker:** `.dockerignore` com `.env`, `.env.*`, `.venv`, `.git`, `__pycache__` e `.pytest_cache`; imagem base `python:3.12-slim` com `uv` e `uv sync --frozen --no-dev`.
- **CI:** workflow do GitHub Actions (`.github/workflows/testes.yml`) com `uv sync --locked` e `uv run pytest`, em todo PR para a `develop` ou a `main` e em todo push na `develop`. Python 3.12, a versão mínima do `pyproject.toml` e a da imagem base. Os testes do Whisper e os de navegador ficam de fora pelo `addopts` do `pyproject.toml` e rodam só na máquina local. Decisões de 24/11:
  - **`uv run pytest`, não `-m "not whisper"`:** o `-m` da linha de comando substitui o do `addopts`, e os testes de navegador voltariam para a CI (sem o Chromium, seriam pulados).
  - **Cache:** o do `uv` (chave pelo `uv.lock`) e o do Hugging Face com só o `multilingual-e5-base`. Rodando a suíte com o cache de modelos vazio e o download bloqueado, só os testes de `test_indice.py` falharam, então nenhum outro modelo é baixado. O push na `develop` existe para o cache: o cache criado num PR só vale para aquele PR.
  - **Para não gastar execuções:** um push novo no mesmo PR cancela a execução anterior, e PR em rascunho não roda. Rodar também em PRs só de documentação foi mantido: pular esses PRs deixaria o check pendente se ele virar obrigatório para o merge.
  - **Tempo:** a suíte padrão (1.121 testes) leva 29 s no MacBook Air M4 com Python 3.13 e 61 s com Python 3.12 num ambiente separado. Na CI, a primeira execução também baixa as dependências e o modelo (~1 GB).
  - **Custo:** o repositório é público, e o GitHub Actions não cobra minutos de repositório público.
  - **Segredos:** o workflow não usa nenhum. Os testes trocam o LLM por um falso, e a permissão do token é só de leitura.

### Se a escolha for sem Docker

O `/opsx:update` altera o requisito "Implantação contínua" da spec `plataforma` ("a partir de um único container"), pergunta à equipe o que muda no `openspec/config.yaml` ("em container Docker único"), e o `Dockerfile` (`s2-plataforma-base` 3.1) pode ir para a `s6-producao`.

## Risks / Trade-offs

- [Nenhuma opção que caiba é gratuita sem cartão] → aprovação de gasto e dono da conta resolvidos antes de quinta (lista acima); sem isso, a publicação vai para a S6 e a semana fecha pelo critério de pronto. **Resolvido em 24/11:** o crédito do Azure for Students cobre o plano A sem cartão.
- [Memória real acima de 4 GB] → vetores no build e a reserva `WHISPER_MODELO=base`; ou um plano maior.
- [Partida a frio longa em 2 vCPU] → vetores no build; a medição de latência da S6 é feita com a aplicação acordada, e o tempo de acordar é registrado à parte.
- [Mudança do torch no lock quebrar o Windows] → o marcador limita a troca ao Linux, e a tarefa só termina com `uv sync` e `uv run pytest` numa máquina Windows.
- [Logs de borda da plataforma (IP, URL) fora do nosso controle] → registrar na decisão o que a plataforma guarda; a aplicação não põe texto na URL.
- [URL pública e Space público expõem o código] → o repositório no GitHub já é público; nenhum segredo nem dado real está versionado.

## Migration Plan

Primeira publicação: não há versão anterior. Para voltar atrás, a plataforma permite reimplantar o commit anterior ou pausar o serviço. A chave do DeepSeek pode ser revogada a qualquer momento no painel do DeepSeek.

## Open Questions

- ~~Região do servidor na plataforma escolhida (Brasil ou EUA/Europa): afeta a latência, não o desenho; registrar na decisão de quinta.~~ Resolvida em 24/11: brazilsouth (seção "Decisão (24/11, tarefa 1.1)").
