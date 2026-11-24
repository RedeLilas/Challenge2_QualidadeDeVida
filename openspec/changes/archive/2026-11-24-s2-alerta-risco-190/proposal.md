# Proposal

## Why

O risco central do projeto é subestimar um perigo real. A orientação de ligar 190 precisa existir antes que qualquer resposta do LLM chegue à usuária na URL publicada. Por ser determinística, essa regra também é a parte mais simples de construir e testar, por isso entra já na S2.

Métricas do ROADMAP afetadas: sensibilidade para risco alto (100%, nenhum falso negativo) e tempo até o 190 (≤ 2 s).

## What Changes

- Arquivo versionado `regras/risco_imediato.json` com padrões de risco imediato, compartilhado entre a PWA e o backend.
- Normalização de texto (minúsculas, sem acentos, espaços colapsados) idêntica nos dois lados.
- Verificação no backend antes de qualquer chamada ao LLM.
- Verificação na PWA antes do envio, funcionando offline.
- Tela de alerta com botão "Ligar 190" (`tel:190`) e o Ligue 180 como opção secundária.
- Suíte de testes com frases fictícias de risco e de não risco.

Requisitos implementados (specs da base): `triagem-risco` (Alerta de risco imediato; Regras de risco auditáveis) e `interface-pwa` (alerta disponível sem conexão).

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

Nenhuma. A mudança implementa requisitos já definidos em `s1-definicoes-base`.

## Impact

- Depende de `s2-plataforma-base` (rota de mensagem e PWA).
- **Privacidade (LGPD):** a verificação roda no aparelho e no servidor sem armazenar a mensagem.
- **Segurança da usuária:** é a principal proteção do sistema; uma falha aqui é uma falha crítica.
- **Fora desta mudança:** a triagem pelo Fonar (`s3-triagem-fonar`) e a detecção de risco por LLM (não planejada: o risco imediato é sempre por regra).
