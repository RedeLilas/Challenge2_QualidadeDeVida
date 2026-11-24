# Casos fictícios de áudio

Casos da `s5-entrada-audio` (tarefa 1.2), descritos em `casos_audio.yaml`.

- **Textos fictícios**, escritos pela equipe (design da `s5-entrada-audio`, decisão de 24/11). Nenhum relato real.
- **Voz sintética offline:** os arquivos foram gerados em 24/11/2026 com o sintetizador do macOS (`say`, voz Luciana, pt-BR), sem internet e sem a voz de ninguém. Quem da equipe concordar pode gravar os mesmos textos pela PWA e trocar o arquivo, mantendo o nome e o formato.
- **Formatos dos dois navegadores:**
  - `.webm` (opus, 48 kHz): o formato do Chrome no Android;
  - `.mp4` (aac): o formato do Safari no iPhone.
  
  São arquivos convertidos, não gravados nos aparelhos. As gravações reais no iPhone são o item 4 da ordem de corte da S5.
- **A7** é silêncio de 5 s, e a transcrição esperada é vazia.
- **A8** (arquivo corrompido e arquivo acima do limite) não fica aqui: o teste gera esses arquivos.

## Gerar de novo

```bash
uv run python scripts/gerar_audios_sinteticos.py              # só no macOS; voz padrão: Luciana
uv run python scripts/gerar_audios_sinteticos.py --voz Flo    # outra voz pt-BR do `say -v '?'`
uv run pytest tests/test_casos_audio.py
```

## Conferência com o Whisper (24/11/2026)

Com o `small` em int8, `language="pt"`, `vad_filter=True` e `beam_size=1`, num Mac do laboratório, os 7 casos deram a transcrição esperada: as palavras-chave aparecem, A5 e A6 disparam a regra de risco, e A7 sai vazio. A transcrição foi feita com o áudio decodificado à parte, porque o `faster-whisper` 1.2.1 chama o PyAV com `metadata_errors`, que o `av` 19.0.2 travado no `uv.lock` não aceita (ver a tarefa 1.3).
