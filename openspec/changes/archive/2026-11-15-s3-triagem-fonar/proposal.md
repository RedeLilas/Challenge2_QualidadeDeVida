# Proposal

## Why

Hoje o sistema só detecta risco imediato em texto livre. A usuária ainda não tem como avaliar o nível de urgência da própria situação. A triagem derivada do Fonar cobre essa lacuna sem depender de LLM e sem enviar nada ao servidor, o que importa quando o agressor pode ter acesso ao celular.

Métrica do ROADMAP afetada: sensibilidade para risco alto (100%, nenhum falso negativo), medida na S4 para a triagem.

## What Changes

- Triagem sem pontuação, com regras em arquivo versionado e no máximo 13 perguntas, com os gatilhos primeiro.
- Encerramento no primeiro gatilho alto.
- Níveis: alto, atenção e sem sinais graves. A usuária nunca vê "risco baixo".
- Novo resultado "não foi possível descartar risco alto", com as orientações do nível alto, quando há pulo ou "não sei" em um dos quatro gatilhos.
- Execução só no navegador, com respostas só em memória, texto fixo sem LLM e aviso de limite em todo resultado.
- Botão próprio na PWA, acessível sem o formulário de perfil.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `triagem-risco`: define níveis, gatilhos, resultado de risco alto não descartado e execução só no navegador, e troca "risco baixo" por "sem sinais graves".

## Impact

- **Novos arquivos:** `regras/triagem_fonar.json`, `web/triagem.js`, testes em `tests/`.
- **Código alterado:** `web/sw.js` (funcionar sem internet), `web/index.html` e `web/app.js` (tela da triagem).
- **Depende de:** navegação de `s3-frontend-e-perfil`. Depende também da conferência do PDF oficial do Fonar.
- **Privacidade (LGPD):** nenhuma resposta sai do aparelho nem é gravada. Nenhum dado identificador é pedido.
- **Segurança da usuária:** regras determinísticas e conservadoras, e a saída rápida apaga as respostas em memória. Esta triagem não substitui a avaliação profissional, e todo resultado diz isso.
- **Fora desta mudança:** agente de triagem do orquestrador (S4), itens não adaptáveis do Fonar, lista por região dos serviços (S4).
