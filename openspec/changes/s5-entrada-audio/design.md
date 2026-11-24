# Design

## Context

- A conversa envia texto ao `POST /orquestrar` (`web/app.js`, `enviar()`). Antes de qualquer envio, o navegador roda a regra de risco (`web/risco.js`, mesmas regras de `regras/risco_imediato.json` e mesma normalização de `app/risco.py`). Com sinal de risco, mostra o 190 e só envia depois do toque em "Continuar com minha pergunta" (decisão de 17/11). O servidor repete a checagem.
- O servidor já carrega o índice do RAG em segundo plano ao subir (`app/main.py`, cerca de 20 s em CPU; pico de 2,5 GB medido em 09/11). O middleware de `app/logs.py` registra só método, rota, status, duração e o tipo do erro.
- O DeepSeek só aceita texto. A decisão de LGPD de 09/11 (opção (c)) vale para o texto que vai ao LLM; o áudio não tinha decisão até aqui.
- A equipe tem só a terça (24/11) para esta mudança; o deploy é da `s5-deploy`, na quinta.

## Goals / Non-Goals

**Goals:**
- Pergunta por áudio respondida de ponta a ponta na máquina local (critério de pronto da S5).
- O áudio fica só no servidor da aplicação, em memória, e nada dele ou da transcrição vai a disco, log ou serviço externo.
- O alerta de 190 continua por regra, sem LLM, e o texto com risco não chega ao LLM sem o toque.
- Medir o pico de memória e os tempos de carga do RAG com o Whisper, para a decisão de plataforma de quinta.

**Non-Goals:**
- Fotos e leitura de documento (decisão de 24/11).
- Resposta falada, gravação contínua e detecção automática do fim da fala.
- Medir o tempo até o 190 e o p95 no celular e na URL publicada (`s6-producao`).

## Decisions

### Transcrição com Whisper no servidor da aplicação (decisão de 24/11)

| Opção | Para onde vai o áudio | Motivo |
| :--- | :--- | :--- |
| **Whisper no servidor da aplicação** (escolhida) | Só ao nosso servidor, em memória | Nenhum terceiro recebe a voz; o mesmo modelo em todos os celulares; custo só de memória e CPU no deploy |
| Web Speech API do navegador (descartada) | Ao Google (Chrome/Android) ou à Apple (Safari/iOS), conforme o navegador | Envia a voz a um serviço externo sem decisão de LGPD possível da nossa parte, e o comportamento muda de aparelho para aparelho |
| Whisper no navegador (WebAssembly/WebGPU) (descartado) | Fica no aparelho | Baixa de 40 a 250 MB de modelo no celular, guarda o modelo no aparelho (rastro de uso e espaço) e é lento demais em Android de entrada, contrariando `interface-pwa` (celular básico, 3G) |
| API de transcrição externa (descartada) | Ao provedor | Mesma objeção da Web Speech API; seria outra transferência internacional de dados (LGPD, art. 33) |

### faster-whisper, modelo `small` em int8 (decisão de 24/11)

Comparação feita antes da decisão (ordens de grandeza dos benchmarks publicados pelos projetos e do artigo do Whisper; a medição real é a tarefa 5.1):

| Implementação | Modelo | Memória extra | 30 s de áudio, 8 threads | 30 s de áudio, 2 vCPU | Português (WER aprox.) | Torch |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| faster-whisper (int8) | tiny | ~0,15 GB | < 1 s | ~2 s | fraca (~30%) | não |
| | base | ~0,25 GB | ~1,5 s | ~4 s | regular (~18%) | não |
| | **small** | ~0,6 GB | ~4 s | ~10 s | boa (~10%) | não |
| | medium | ~1,5 GB | ~10 s | ~30 s | muito boa (~6%) | não |
| whisper.cpp | tiny a medium | 0,3 a 2,1 GB | ~1,5x o faster-whisper | idem | igual | não (build C++ ou bindings com pouco suporte no Windows) |
| openai-whisper (fp32) | tiny a medium | 0,4 a 4 GB | ~4x o faster-whisper | `small` passa de 30 s | igual | sim |

Motivo: menor memória e menor latência em CPU, sem torch, com rodas para Windows, macOS e Linux, e leitura de webm/opus (Chrome/Android) e mp4/aac (Safari/iPhone) pelo PyAV, sem ffmpeg no sistema. O `small` é o menor modelo com qualidade boa em português para termos como "medida protetiva" e "Maria da Penha".

Configuração: `WHISPER_MODELO` (padrão `small`), `language="pt"` fixo (sem detecção de idioma, que custa tempo e erra em falas curtas), `vad_filter=True` (corta o silêncio antes de transcrever), `beam_size=1` e `cpu_threads` igual ao número de vCPUs. **Reserva:** se a medição na plataforma escolhida passar de ~5 s para 30 s de áudio, `WHISPER_MODELO=base` troca o modelo sem mudar código. A meta da S6 é p95 ≤ 10 s para a resposta inteira, e o LLM e o RAG levam de 2 a 4 s.

### Rota `POST /transcrever`

- Corpo: o áudio cru, com o `Content-Type` do `MediaRecorder` (`audio/webm`, `audio/ogg` ou `audio/mp4`). Não usa `multipart/form-data`, o que evita a dependência `python-multipart` e não grava partes em arquivo temporário.
- O servidor lê no máximo 1 MB (confere o `Content-Length` e corta a leitura em 1 MB + 1 byte), decodifica em memória (`io.BytesIO` → PyAV → amostras de 16 kHz), confere a duração (até 35 s: 30 s de limite com 5 s de tolerância para o cabeçalho e o fim da gravação) e transcreve.
- Resposta: `{"texto": "..."}` com `Cache-Control: no-store`. Erros: 413 (tamanho), 422 (duração, arquivo ilegível ou sem fala), 503 (modelo ainda carregando ou indisponível), sempre com a mensagem pronta para a tela e sem o conteúdo.
- **Nenhum arquivo:** o caminho principal não cria arquivo. Se uma versão do PyAV exigir arquivo, o temporário é criado com `tempfile.NamedTemporaryFile(delete=False)` dentro de `try/finally`, que o apaga sempre. O teste confere que nenhum arquivo novo aparece no diretório temporário nem no diretório de trabalho, com sucesso e com falha.
- **Sem regra e sem LLM na rota:** o servidor só transcreve. A rota não importa o cliente de LLM nem o índice, e o teste usa um LLM falso que falha se for chamado.
- **Modelo carregado ao subir**, em segundo plano, como o índice do RAG (`_ciclo_de_vida` em `app/main.py`), para o primeiro áudio não esperar a carga. Uma trava garante uma única carga e uma transcrição por vez, o que limita a memória; um segundo pedido espera. Enquanto o modelo carrega, a rota responde 503 com "A transcrição ainda está iniciando; tente em alguns segundos ou digite".

### Limites: 30 s e 1 MB

Perguntas faladas de 15 a 30 s cobrem os exemplos das personas. Com o `small` em 2 vCPU, 30 s de áudio já levam ~10 s para transcrever; um limite maior estouraria o orçamento de tempo. O opus do Chrome grava cerca de 32 kbit/s (~120 KB em 30 s) e o AAC do Safari até 128 kbit/s (~480 KB); 1 MB dá folga sem aceitar arquivos grandes. Mensagem para quem passar: "O áudio pode ter até 30 segundos. Grave de novo, em partes, ou digite sua pergunta." A gravação para sozinha em 30 s, com contagem regressiva visível.

### Alerta de 190 e a exceção à decisão de 17/11

Fluxo (decisão de 24/11):

1. A usuária grava. O navegador envia o áudio ao `/transcrever`.
2. O servidor só transcreve e devolve o texto. Não aplica regra, não chama o LLM, não guarda e não registra nada.
3. Ao receber o texto, o navegador roda `Risco.avaliar` na hora.
   - Com sinal de risco: mostra o alerta de 190 com "Continuar com minha pergunta", e o texto só vai ao `/orquestrar` depois do toque, como no texto digitado.
   - Sem sinal de risco: põe a transcrição na caixa de texto para conferir. Ao tocar em enviar, a regra roda de novo (`enviar()`), e segue o fluxo do texto digitado.
4. O `/orquestrar` continua checando o risco no servidor.

**Exceção à decisão de 17/11.** A decisão diz que texto com sinal de risco só vai ao servidor depois do toque em "Continuar". No áudio isso é impossível: a regra precisa de texto, e o texto só existe depois da transcrição no servidor. A exceção vale só para o `/transcrever` e é mitigada assim: a rota só transcreve; o áudio não é guardado, não vai a log nem a serviço externo; nenhum agente nem o LLM é chamado antes do toque. A exceção fica registrada aqui, no ROADMAP (24/11) e no requisito "Continuar depois do alerta de 190" da spec `conversa`.

**Tempo até o 190.** No áudio, a meta de ≤ 2 s conta a partir da chegada da transcrição ao aparelho. O envio e a transcrição levam alguns segundos antes disso, e quem está em perigo imediato tem o 190 visível no topo da tela antes de gravar. A medição no celular é da `s6-producao`.

### Transcrição na caixa para conferir (recomendada e adotada)

Erros do Whisper em nomes e termos jurídicos ("medida protetiva", "Maria da Penha") mudam a resposta jurídica sem que a usuária perceba. Colocar a transcrição na caixa que já existe custa quase nada no prazo: é mais simples que enviar direto, cerca de 1 a 2 horas com o teste. Dois cuidados: o alerta de 190 não espera a conferência, e a saída rápida já esvazia a caixa (`apagarConversa()` limpa `campo`); um teste confere isso.

### Navegador: `web/audio.js`

- `getUserMedia({audio: true})` só no toque do botão. `MediaRecorder` com o primeiro formato aceito entre `audio/webm;codecs=opus`, `audio/ogg;codecs=opus` e `audio/mp4`. Os pedaços ficam num array em memória.
- Ao parar, por toque ou pelo limite: junta o `Blob`, desliga todas as trilhas do microfone (o indicador se apaga), envia com `fetch(..., {cache: "no-store"})` e limpa as referências. Nada vai a `localStorage`, IndexedDB, Cache API ou download; o service worker já ignora pedidos que não são GET.
- `Audio.cancelar()` é chamado por `sair()` e `apagarConversa()`: para o gravador, desliga o microfone, descarta os pedaços e aborta o pedido em andamento. Uma transcrição que chegue depois disso é ignorada.
- Sem internet (`navigator.onLine` falso), o botão fica desabilitado com "Para usar o áudio, é preciso internet. Digite sua pergunta."
- O arquivo segue o padrão de `web/risco.js` e `web/rede.js` (sem armazenamento, testável em QuickJS no que não depende do navegador: escolha do formato, contagem do limite e decisão "alerta ou caixa" ao receber o texto).

### Logs

O middleware de `app/logs.py` já não registra corpo. O que muda: o logger `faster_whisper` fica em `WARNING` (no `INFO` ele registra a duração e o idioma, e versões futuras podem registrar mais), e a rota não registra nada além do middleware. O teste usa `caplog` no nível `DEBUG` para todos os loggers e confere que nenhuma palavra da transcrição fictícia nem bytes do áudio aparecem, com sucesso e com falha. O uvicorn com `--no-access-log` continua obrigatório (design da `s2-plataforma-base`); a publicação é da `s5-deploy`.

### Casos fictícios de áudio (decisão de 24/11)

Ficam em `tests/audios/`, com `casos_audio.yaml` (arquivo, texto lido, palavras-chave obrigatórias, risco esperado e agente esperado) e um `LEIAME.md` dizendo que os textos são fictícios, escritos pela equipe, e lidos por membros da equipe que concordaram, ou gerados por voz sintética offline. Nenhuma voz ou relato real.

| Caso | Texto | Verificação objetiva |
| :--- | :--- | :--- |
| A1 | "Ele pode tirar meus filhos de mim?" | Transcrição normalizada contém "tirar" e "filhos"; vai ao jurídico |
| A2 | "Tenho direito ao Bolsa Família?" | Contém "bolsa familia"; vai a benefícios |
| A3 | "Como funciona a medida protetiva?" | Contém "medida protetiva" |
| A4 | "Minha amiga apanha do marido, como eu posso ajudar?" | Contém "amiga" e "ajudar" |
| A5 (risco) | "Ele está aqui na porta com uma faca e disse que vai me matar" | `risco.avaliar` dispara (`arma` ou `ameaca_morte`); LLM falso não chamado sem `alerta_visto` |
| A6 (risco + pergunta) | "Ele disse que vai me matar hoje, posso pedir medida protetiva?" | O 190 dispara; depois do "Continuar", vai ao jurídico |
| A7 | 5 s de silêncio ou ruído | Transcrição vazia; mensagem "Não entendi o áudio" |
| A8 | Arquivo corrompido e arquivo acima do limite (gerados no teste) | Erro com mensagem; nenhum arquivo no disco |

As frases de A5 e A6 disparam a regra atual (conferido em 24/11). Pelo menos um áudio gravado no Android (webm/opus) e um no iPhone (mp4/aac). Os testes que usam o Whisper de verdade levam a marca `whisper` e rodam na máquina local (`uv run pytest -m whisper`), porque baixam ~0,5 GB; a suíte padrão usa um transcritor falso.

## Risks / Trade-offs

- [Latência do `small` em 2 vCPU perto de 10 s para 30 s de áudio] → medir na tarefa 5.1 e na plataforma escolhida; trocar para `base` por variável de ambiente.
- [Memória: RAG (2,5 GB) + Whisper pode passar do plano escolhido] → medir o pico juntos (tarefa 5.1) e registrar no design da `s5-deploy` antes da decisão de quinta.
- [Instalação do faster-whisper quebrar o `uv.lock` ou o Windows] → a tarefa 1.1 só termina com `uv sync` e `uv run pytest` passando em uma máquina Windows da equipe.
- [Exceção à decisão de 17/11: a fala com risco chega ao servidor antes da regra] → só transcrição, sem guarda, sem log, sem serviço externo e sem LLM antes do toque; registrada no ROADMAP.
- [Erros de transcrição] → a usuária confere o texto na caixa antes de enviar.
- [Gravar em voz alta pode expor a usuária] → o botão não grava sozinho, a saída rápida interrompe a gravação, e o texto continua sendo o caminho principal.
- [Formatos diferentes entre Android e iPhone] → casos gravados nos dois, e o PyAV lê os dois sem ffmpeg.
- [Voz dos membros da equipe no repositório] → só quem concordar grava; a voz sintética é alternativa aceita.

## Migration Plan

Mudança aditiva: o botão de microfone só aparece com a rota disponível. Para voltar atrás, basta esconder o botão; a conversa por texto não muda. O modelo `small` é baixado na primeira carga local; no deploy, no build (`s5-deploy`). Pela spec `plataforma`, esta mudança só é arquivada depois de publicada.
