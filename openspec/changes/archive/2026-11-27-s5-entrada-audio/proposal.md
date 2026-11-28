# Proposal

## Why

O entregável da S5 é "agentes multimodais", e a spec `conversa` já prevê a pergunta por áudio sem guardar o arquivo. Falar é mais rápido que digitar para quem está com pressa, com medo ou com pouca familiaridade com a escrita, e o DeepSeek só aceita texto, então a transcrição precisa de um componente próprio. A equipe tem só dois dias nesta semana (terça, 24/11, e quinta, 26/11) e decidiu em 24/11 ficar só com texto e áudio, sem fotos.

Métrica do ROADMAP: critério de pronto da S5 ("uma pergunta por áudio é respondida de ponta a ponta"). A mudança também afeta o **tempo até o 190 (≤ 2 s)**, porque no áudio a regra só roda depois da transcrição, e o **tempo de resposta (p95 ≤ 10 s)**, medidos na S6.

## What Changes

- Botão de microfone na conversa. A permissão do microfone só é pedida no toque, e a gravação fica só na memória da aba, com limite de **30 s** de duração e contagem regressiva.
- Rota nova `POST /transcrever` no **servidor da própria aplicação**: recebe o áudio, transcreve com o Whisper (faster-whisper, modelo `small` em int8, português fixo) e devolve só o texto. O áudio **nunca vai a um serviço externo e nunca é guardado**: é processado em memória, sem arquivo no disco, e nada do áudio nem da transcrição vai aos logs. A resposta usa `Cache-Control: no-store`.
- Limites no servidor: até **1 MB** e **30 s** (com 5 s de tolerância). Acima disso, a usuária vê "O áudio pode ter até 30 segundos. Grave de novo, em partes, ou digite sua pergunta."
- Alerta de 190: o servidor só transcreve, sem regra e sem LLM. Quando o texto chega, o navegador roda a regra de risco de `web/risco.js` na hora. Com sinal de risco, aparece o alerta com "Continuar com minha pergunta", e nada vai ao `/orquestrar` sem o toque. Sem sinal de risco, a transcrição vai para a caixa de texto, para a usuária conferir e enviar. Daí em diante vale o fluxo do texto digitado.
- **Exceção à decisão de 17/11** ("texto com sinal de risco só vai ao servidor depois do toque"): o áudio chega ao servidor antes de qualquer regra, porque a regra precisa de texto. A exceção é registrada no design, no ROADMAP (24/11) e na spec `conversa`.
- A saída rápida interrompe uma gravação em andamento, desliga o microfone e descarta o áudio.
- Casos fictícios de áudio (textos escritos pela equipe, lidos por membros da equipe que concordaram ou gerados por voz sintética) em `tests/audios/`, com verificação por palavras-chave e pela regra de risco.
- Remoção do requisito "Leitura de documento fotografado" da spec `conversa` (decisão de 24/11).
- Última tarefa: medir o pico de memória com o RAG e o Whisper carregados juntos e os tempos de carga, e registrar no design da `s5-deploy`.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `conversa`: a pergunta por áudio passa a ter transcrição no servidor da aplicação, limites, conferência da transcrição e alerta de 190 pela regra sobre o texto transcrito; "Continuar depois do alerta de 190" registra a exceção do áudio; sai o requisito "Leitura de documento fotografado".
- `privacidade-seguranca`: o áudio nunca é guardado nem registrado em log e nunca vai a serviço externo; microfone só no toque, nada do áudio salvo no aparelho, e a saída rápida interrompe a gravação.

## Impact

- **Arquivos novos:** `app/transcricao.py`, `web/audio.js`, `tests/test_transcricao.py`, `tests/audios/` (casos, `casos_audio.yaml` e `LEIAME.md`).
- **Arquivos alterados:** `app/main.py` (rota `/transcrever` e carga do Whisper em segundo plano), `web/app.js` (botão de microfone, chegada da transcrição e saída rápida), `web/index.html`, `web/styles.css`, `web/sw.js` (versão do cache e `web/audio.js`), `tests/test_pwa.py`, `pyproject.toml` e `uv.lock` (`faster-whisper`), `README.md`.
- **Dependências:** `faster-whisper` (CTranslate2, PyAV para ler webm/opus e mp4/aac sem ffmpeg, onnxruntime para o filtro de silêncio). O modelo `small` (~0,5 GB) é baixado do Hugging Face na primeira carga; no deploy, no build (`s5-deploy`).
- **Memória do deploy:** cerca de 0,6 GB a mais que o RAG (estimativa: ~3,1 GB no total), a medir na última tarefa.
- **Privacidade (LGPD):** o áudio e a voz são dados pessoais e podem conter o relato. Eles vão só ao servidor da aplicação, sem serviço externo, e não são guardados nem registrados. A transcrição segue o caminho do texto digitado, inclusive a decisão de LGPD de 09/11 (opção (c): só casos fictícios vão ao DeepSeek). Os áudios de teste são fictícios e gravados com consentimento de quem leu, ou sintéticos.
- **Segurança da usuária:** o alerta de 190 continua por regra, sem LLM, e aparece assim que a transcrição chega; o texto com risco não chega ao LLM sem o toque em "Continuar". Gravar em voz alta pode expô-la a quem está por perto: o botão não grava sozinho, e a saída rápida interrompe a gravação. Sem internet, o áudio não funciona e a tela pede para digitar; o alerta de 190 do texto digitado continua offline.
- **Fora desta mudança:** fotos e leitura de documento (decisão de 24/11); Web Speech API e Whisper no navegador (descartados no design); resposta em áudio (texto para fala); gravação contínua ou detecção automática de fim de fala; o deploy e a medição na URL publicada (`s5-deploy`); a medição do tempo até o 190 e do p95 no celular (`s6-producao`).
