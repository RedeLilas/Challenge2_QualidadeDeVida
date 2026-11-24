# Tasks

As tarefas de empacotar e publicar ficam genéricas até a decisão da tarefa 1.1. Depois dela, o `/opsx:update` as troca pelas da plataforma escolhida.

## 1. Decisão (quinta, 26/11, primeira tarefa)

- [ ] 1.1 Decidir a plataforma e o uso de Docker com a tabela do design, a memória medida (tarefa 5.1 da `s5-entrada-audio`) e a lista "O que precisa estar pronto antes da decisão", registrar a escolha e o motivo no design (seção "Decisão (26/11)", com região e logs de borda da plataforma) e rodar `/opsx:update`; se a escolha for sem Docker, o update altera a spec `plataforma` ("a partir de um único container"), pergunta à equipe sobre o `openspec/config.yaml` e pode mover o `Dockerfile` para a S6 (vem de `s2-plataforma-base` 4.1); verificação: o design tem a decisão com o motivo, as tarefas 2 e 3 citam a plataforma, e `openspec validate s5-deploy` passa

## 2. Empacotar (quinta, 26/11)

- [ ] 2.1 Apontar o torch para o índice só de CPU no Linux (`[[tool.uv.index]]` com `explicit = true` e marcador `sys_platform == 'linux'`); verificação: `uv lock` passa, `uv sync` e `uv run pytest` passam no macOS e numa máquina Windows da equipe, e a instalação no Linux não traz pacotes `nvidia-*`
- [ ] 2.2 Empacotar a aplicação conforme a tarefa 1.1, com os modelos `multilingual-e5-base` e Whisper baixados no build e `HF_HUB_OFFLINE=1` ao subir; só com Docker, criar o `.dockerignore` com `.env`, `.env.*`, `.venv`, `.git`, `__pycache__` e `.pytest_cache` (vem de `s2-plataforma-base` 3.1); verificação: o pacote sobe com o download de modelos bloqueado e responde em `/saude`, numa pergunta jurídica e numa transcrição; com Docker Desktop disponível, `docker run` faz o mesmo localmente
- [ ] 2.3 Gerar os vetores do índice no build e carregá-los ao subir, recalculando só se o resumo dos trechos ou do modelo não bater; verificação: teste confere que o índice carregado dos vetores prontos devolve os mesmos trechos que o montado na hora para as 10 perguntas de `tests/perguntas_juridicas.yaml`, e a partida a frio cai na medição da tarefa 3.2; se não couber no dia, registrar no ROADMAP que vai para a `s6-producao`
- [ ] 2.4 Criar o workflow de CI com `uv sync` e `uv run pytest -m "not whisper"`, com cache do `uv` e dos modelos (vem de `s2-plataforma-base` 3.2); verificação: o workflow passa num PR para a `develop`

## 3. Publicar e verificar (quinta, 26/11)

- [ ] 3.1 Publicar na plataforma escolhida com a chave do DeepSeek só como variável secreta e o uvicorn com `--no-access-log` (vem de `s2-plataforma-base` 3.3); verificação: a URL de teste abre a PWA no celular, a chave não aparece no pacote nem nos logs de build, e uma requisição com query string fictícia não deixa a query string, o IP nem o texto nos logs da aplicação
- [ ] 3.2 Medir na plataforma a partida a frio (do início do processo até `/saude` e até o índice e o Whisper ficarem prontos) e a memória em uso, e registrar no design; verificação: o design tem data, plano e os tempos medidos
- [ ] 3.3 Verificar na URL publicada, com roteiro registrado no design: a pergunta da persona Camila respondida com o art. 7º citado (vem de `s2-rag-juridico` 2.4), uma pergunta por áudio (caso A1) respondida de ponta a ponta no celular, o caso A5 falado mostrando o 190 e a saída rápida; verificação: roteiro preenchido no design, com data e aparelho
- [ ] 3.4 Rodar a suíte inteira, incluindo a de risco/190, e `openspec validate --all`; verificação: os dois passam

## Workflow follow-up

- Arquivar a `s5-deploy` e, em seguida, a `s5-entrada-audio`, que só pode ser arquivada depois de publicada (spec `plataforma`).
- Se a publicação não terminar na quinta, a semana fecha pelo critério de pronto da S5, e a publicação passa para a `s6-producao`, com as duas mudanças ainda abertas.
- Atualizar o status no `ROADMAP.md`.
