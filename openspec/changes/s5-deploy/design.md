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

Fontes (consultadas em 24/11; as páginas do HF, do Render, do Railway e do Koyeb foram lidas, e as da Fly.io e do Cloud Run, por busca): [HF Spaces overview](https://huggingface.co/docs/hub/spaces-overview), [HF Docker Spaces](https://huggingface.co/docs/hub/spaces-sdks-docker), [HF hardware](https://huggingface.co/docs/hub/en/spaces-gpus), [HF pricing](https://huggingface.co/pricing), [Render compute plans](https://render.com/docs/compute-plans), [Render free](https://render.com/docs/free), [Railway plans](https://docs.railway.com/reference/pricing/plans), [Fly.io pricing](https://docs.fly.io/about/pricing), [Cloud Run pricing](https://cloud.google.com/run/pricing), [Koyeb pricing](https://www.koyeb.com/pricing).

**Achado de 09/11 conferido em 24/11:** confirmado. A documentação oficial diz que "Gradio and Docker Spaces run on compute and require a paid plan to create: PRO for personal accounts, Team or Enterprise for organizations". O CPU Basic continua com 2 vCPU, 16 GB e "Free!" por hora, e dorme depois de 48 h sem uso. A recomendação da S2 (HF Spaces grátis) não vale mais sem o PRO.

**Leitura para quinta (recomendação preliminar, não é a decisão):** o HF Spaces com PRO é a opção mais barata que cabe com folga (US$ 9/mês, 16 GB) e tem o menor esforço, mas exige Docker e a conta PRO de uma pessoa da equipe (ou Team na organização). A Fly.io (~US$ 25/mês) e o Railway (~US$ 35 a 45/mês) são as reservas com Docker ou nativo. O Cloud Run sai quase de graça com pouco uso, mas cada acordar paga a carga do índice e do Whisper, o que atrapalha a medição da S6. O Render só cabe no plano de 4 GB, o mais caro da tabela.

### O que precisa estar pronto antes da decisão de quinta

- [ ] Memória e tempos medidos (tarefa 5.1 da `s5-entrada-audio`), na tabela abaixo.
- [ ] Aprovação de gasto: quanto por mês e até quando (a S7 termina em 11/12), e quem aprova.
- [ ] Dono da conta e do cartão: conta pessoal (HF PRO, Fly.io) ou da organização `RedeLilas` (HF Team, Railway com time).
- [ ] Acessos: quem da equipe entra na plataforma e quem vê os segredos.
- [ ] Chave do DeepSeek para o ambiente publicado: de quem é, com limite de gasto, e só casos fictícios (opção (c) de 09/11).
- [ ] Permissões no GitHub da organização para o workflow de CI e, se a plataforma pedir, para a integração de deploy.
- [ ] Créditos de estudante (ex.: GitHub Student Developer Pack, Azure for Students), se alguém da equipe tiver: não conferidos em 24/11.
- [ ] Docker Desktop em ao menos uma máquina (ajuda a testar a imagem, mas não é obrigatório).

### Memória e tempos medidos (preenchido pela tarefa 5.1 da `s5-entrada-audio`)

| Medida | Valor | Máquina, data e comando |
| :--- | :--- | :--- |
| Pico de memória com o RAG e o Whisper carregados juntos | a medir | |
| Carga do índice (montagem dos vetores) | a medir | |
| Carga do Whisper `small` | a medir | |
| Transcrição de A1 a A6, todas as threads (média e máximo) | a medir | |
| Transcrição de A1 a A6, 2 threads (média e máximo) | a medir | |

### Requisitos com ou sem Docker

- **Torch só para CPU no Linux:** índice `pytorch-cpu` (`https://download.pytorch.org/whl/cpu`) declarado em `[[tool.uv.index]]` com `explicit = true`, e `[tool.uv.sources]` apontando o torch para ele só com o marcador `sys_platform == 'linux'`. No Windows e no macOS o torch continua vindo do PyPI, então o ambiente local não muda. Alternativa descartada: trocar o torch para CPU em todas as plataformas, o que muda o lock de todo mundo sem ganho fora do Linux.
- **Modelos no build:** um script baixa `intfloat/multilingual-e5-base` e o Whisper (`Systran/faster-whisper-small`, ou o modelo de `WHISPER_MODELO`) para o cache do Hugging Face dentro do pacote, e a aplicação sobe com `HF_HUB_OFFLINE=1`. Assim, subir não depende do Hugging Face e não faz chamada externa.
- **Partida a frio:** medida do início do processo até `/saude` e até o índice e o Whisper ficarem prontos. Em 2 vCPU, a montagem dos vetores deve levar bem mais que os ~20 s da máquina de 28 núcleos.
- **Vetores no build, se couber no dia:** o build gera a matriz de vetores (`numpy.save`) junto com um resumo dos trechos (`dados/leis/*.jsonl`) e do modelo; ao subir, o índice carrega a matriz se o resumo bater e só recalcula se não bater. Isso tira a montagem da partida a frio e deve baixar o pico de memória. Se não couber na quinta, vai para a `s6-producao`.
- **Chave do DeepSeek:** só como variável secreta da plataforma (`LLM_API_KEY`), nunca em `ARG`/`ENV` do build nem em arquivo copiado. O `.env` fica fora do pacote.
- **Servidor:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-access-log`, um único processo (os modelos ficam em memória uma vez só).
- **Só com Docker:** `.dockerignore` com `.env`, `.env.*`, `.venv`, `.git`, `__pycache__` e `.pytest_cache`; imagem base `python:3.12-slim` com `uv` e `uv sync --frozen --no-dev`.
- **CI:** workflow do GitHub Actions com `uv sync` e `uv run pytest -m "not whisper"`, com cache do `uv` e dos modelos do Hugging Face. Os testes do Whisper rodam só na máquina local.

### Se a escolha for sem Docker

O `/opsx:update` altera o requisito "Implantação contínua" da spec `plataforma` ("a partir de um único container"), pergunta à equipe o que muda no `openspec/config.yaml` ("em container Docker único"), e o `Dockerfile` (`s2-plataforma-base` 3.1) pode ir para a `s6-producao`.

## Risks / Trade-offs

- [Nenhuma opção que caiba é gratuita sem cartão] → aprovação de gasto e dono da conta resolvidos antes de quinta (lista acima); sem isso, a publicação vai para a S6 e a semana fecha pelo critério de pronto.
- [Memória real acima de 4 GB] → vetores no build e a reserva `WHISPER_MODELO=base`; ou um plano maior.
- [Partida a frio longa em 2 vCPU] → vetores no build; a medição de latência da S6 é feita com a aplicação acordada, e o tempo de acordar é registrado à parte.
- [Mudança do torch no lock quebrar o Windows] → o marcador limita a troca ao Linux, e a tarefa só termina com `uv sync` e `uv run pytest` numa máquina Windows.
- [Logs de borda da plataforma (IP, URL) fora do nosso controle] → registrar na decisão o que a plataforma guarda; a aplicação não põe texto na URL.
- [URL pública e Space público expõem o código] → o repositório no GitHub já é público; nenhum segredo nem dado real está versionado.

## Migration Plan

Primeira publicação: não há versão anterior. Para voltar atrás, a plataforma permite reimplantar o commit anterior ou pausar o serviço. A chave do DeepSeek pode ser revogada a qualquer momento no painel do DeepSeek.

## Open Questions

- Região do servidor na plataforma escolhida (Brasil ou EUA/Europa): afeta a latência, não o desenho; registrar na decisão de quinta.
