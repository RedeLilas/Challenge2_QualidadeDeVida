# Proposal

## Why

Sem entrevistas com a rede do DF, as informações sobre serviços locais, normas distritais e o modelo atual do Fonar precisam vir de pesquisa documental em fontes oficiais. As mudanças da S3 e da S4 (triagem, benefícios e rede de atendimento) dependem desses dados, por isso o levantamento começa na S2.

Métricas do ROADMAP afetadas: acurácia de elegibilidade (≥ 90%, S4) e sensibilidade para risco alto (100%, S4), que dependem de regras escritas a partir dessas fontes.

## What Changes

- `dados/rede_protecao_df.csv`: serviços da rede de proteção do DF.
- `dados/normas.csv`: normas federais e distritais relevantes, com tema e vigência.
- `dados/fonar/notas.md`: perguntas do modelo vigente do Fonar e quais podem ser adaptadas para autoaplicação.
- Escolha de 1 benefício distrital para modelar na S3.
- Script que valida se todo registro tem fonte oficial e data de verificação.

Requisitos implementados ou preparados (specs da base): `rede-atendimento` (Origem e atualidade do dado), `beneficios` (Regras auditáveis com vigência) e `triagem-risco` (base para a Triagem de urgência baseada no Fonar).

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

Nenhuma. A mudança implementa requisitos já definidos em `s1-definicoes-base`.

## Impact

- Cria a pasta `dados/` com arquivos versionados.
- **Privacidade (LGPD):** só dados públicos de serviços e normas; nenhum dado pessoal.
- **Segurança da usuária:** endereços e telefones errados podem atrasar o atendimento; por isso cada registro tem fonte e data.
- **Fora desta mudança:** CNES (importado na S4), geocodificação por CEP (S4) e implementação das regras (S3).
