# Tasks

## 1. Dependência, casos e transcrição (terça, 24/11)

- [x] 1.1 Adicionar `faster-whisper` ao `pyproject.toml` com `uv add` e atualizar o `uv.lock`; verificação: `uv sync` e `uv run pytest` passam no macOS e numa máquina Windows da equipe, e `uv run python -c "import faster_whisper"` funciona nas duas **(verificado no macOS e no Windows em 24/11; a verificação só testou o import, e o faster-whisper 1.2.1 não decodificava áudio com o av 19 — corrigido no mesmo dia fixando `av>=15,<19`, com teste de decodificação em `tests/test_dependencias_audio.py`)**
- [x] 1.2 Criar `tests/audios/` com `casos_audio.yaml` (arquivo, texto lido, palavras-chave, risco esperado, agente esperado) e `LEIAME.md` (textos fictícios; leitura por membros da equipe que concordaram ou voz sintética offline), e gravar os casos A1 a A7 do design pela PWA ou por voz sintética, com ao menos um arquivo webm/opus (Android) e um mp4/aac (iPhone); verificação: teste de estrutura confere que todo caso tem arquivo existente, texto e palavras-chave, e que os textos de A5 e A6 disparam `risco.avaliar`
- [ ] 1.3 Criar `app/transcricao.py`: carga do modelo por `WHISPER_MODELO` (padrão `small`, int8), decodificação em memória, conferência da duração, transcrição com `language="pt"`, `vad_filter=True` e `beam_size=1`, e o logger `faster_whisper` em `WARNING`; verificação: `uv run pytest -m whisper` confere as palavras-chave de A1 a A6 e a transcrição vazia de A7

## 2. Rota `/transcrever` sem guarda e sem log (terça, 24/11)

- [x] 2.1 Criar `POST /transcrever` em `app/main.py` com corpo cru, limites de 1 MB e 35 s, erros 413/422/503 com a mensagem para a tela, `Cache-Control: no-store`, carga do modelo em segundo plano ao subir e trava de uma transcrição por vez; verificação: testes com transcritor falso cobrem 413, 422 (duração, arquivo ilegível, sem fala), 503 durante a carga e o `no-store`, e um LLM falso que falha se for chamado confirma que a rota não chama o LLM nem monta o índice
- [ ] 2.2 Garantir que nenhum arquivo fica no disco; verificação: teste lista o diretório temporário e o de trabalho antes e depois de uma transcrição com sucesso, de um arquivo corrompido, de um acima do limite e de uma exceção do modelo, e não encontra arquivo novo
- [ ] 2.3 Garantir que nada do áudio nem da transcrição vai aos logs; verificação: teste com `caplog` em `DEBUG` para todos os loggers transcreve A1 (marca `whisper`) e um arquivo corrompido, e confere que nenhuma palavra da transcrição nem bytes do áudio aparecem; outro teste, com o transcritor falso, faz a mesma conferência na suíte padrão

## 3. Gravação no navegador (terça, 24/11)

- [x] 3.1 Criar `web/audio.js`: escolha do formato (`webm/opus`, `ogg/opus` ou `mp4`), limite de 30 s com contagem regressiva, desligar as trilhas do microfone ao parar, `Gravacao.cancelar()` e a decisão ao receber o texto (alerta de 190 ou caixa de texto, por `Risco.avaliar`); incluir no service worker e subir a versão do cache; verificação: testes em QuickJS cobrem a escolha do formato, o limite e a decisão com o texto de A5 (alerta) e de A1 (caixa), e `tests/test_pwa.py` confere que `web/audio.js` não usa `localStorage`, `sessionStorage`, IndexedDB nem Cache API e que o service worker o inclui
- [ ] 3.2 Ligar o botão de microfone em `web/index.html` e `web/app.js`: permissão pedida só no toque, transcrição com risco mostra o alerta com "Continuar com minha pergunta", sem risco vai para a caixa, botão desabilitado sem internet, mensagens de limite e de "Não entendi o áudio", e `sair()` e `apagarConversa()` chamando `Gravacao.cancelar()`; verificação: `tests/test_pwa.py` confere que `getUserMedia` só aparece dentro do tratador do toque, que `sair()` e `apagarConversa()` chamam `Gravacao.cancelar()` e que a chegada da transcrição com risco não chama `fetch` para `/orquestrar`
- [ ] 3.3 Verificação manual no Android e no iPhone, com roteiro registrado no design (data e aparelho): a permissão só aparece no toque, o indicador do microfone se apaga ao parar, a saída rápida durante a gravação para tudo e abre o site neutro, A5 falado mostra o 190 e a aba de rede não mostra pedido ao `/orquestrar` antes do "Continuar"; verificação: roteiro preenchido no design, com cada item marcado

## 4. Ponta a ponta (terça, 24/11)

- [ ] 4.1 Testar o caminho completo: áudio A1 → `/transcrever` → regra sem risco → `/orquestrar` → resposta do jurídico com citação, e áudio A6 → 190 → `/orquestrar` só com `alerta_visto`; verificação: teste com a marca `whisper` e LLM falso passa, e uma pergunta por áudio é respondida de ponta a ponta na máquina local com o LLM local (critério de pronto da S5), registrado no design
- [ ] 4.2 Documentar `WHISPER_MODELO` no `.env.example` e no `README.md` (como gravar os casos e rodar `uv run pytest -m whisper`) e rodar a suíte inteira, incluindo a de risco/190; verificação: `uv run pytest` passa, e os comandos do README rodam como escritos

## 5. Medição para o deploy (terça, 24/11; no máximo quinta de manhã, antes da tarefa 1.1 da `s5-deploy`)

- [ ] 5.1 Medir o pico de memória com o RAG e o Whisper carregados juntos, os tempos de carga (índice e modelo) e o tempo de transcrição de A1 a A6 com todas as threads e com 2 threads (simulando 2 vCPU), e registrar no `design.md` da `s5-deploy` (máquina, data, comando e números); verificação: a tabela "Memória e tempos medidos" do design da `s5-deploy` está preenchida e indica se o `small` cabe no orçamento ou se a reserva `base` é necessária

## Workflow follow-up

- Arquivar só depois de publicada na URL de teste (spec `plataforma`, requisito "Implantação contínua"), o que depende da `s5-deploy`.
- Ao arquivar, tirar "e foto" do `## Purpose` da spec `conversa`, já que o requisito de foto sai com esta mudança.
- Atualizar o status no `ROADMAP.md`.
