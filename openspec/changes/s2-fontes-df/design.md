# Design

## Context

Não haverá entrevistas com a Defensoria, a Casa da Mulher Brasileira ou outros serviços. A pesquisa é feita por 1 ou 2 pessoas em 2 dias, só em fontes públicas.

## Goals / Non-Goals

**Goals:**
- Dados suficientes para a S3 (triagem e benefícios) e a S4 (rede de atendimento).
- Todo registro rastreável até uma fonte oficial com data.

**Non-Goals:**
- Cobertura completa de todos os serviços do DF (o alvo é a rede especializada).
- Implementar regras ou buscas (S3 e S4).

## Decisions

### Fontes aceitas
Apenas fontes oficiais: sites do Governo do DF (`df.gov.br` e secretarias), Polícia Civil do DF, Defensoria Pública do DF, TJDFT, Ministério Público do DF, Planalto, `gov.br` e CNES/DATASUS. Notícias e blogs servem só como pista para achar a fonte oficial.

### `dados/rede_protecao_df.csv`

| Coluna | Exemplo |
| :--- | :--- |
| `nome` | Casa da Mulher Brasileira |
| `tipo` | CMB, CEAM, DEAM, Defensoria, Juizado, outro |
| `ra` | Ceilândia |
| `endereco` | endereço completo |
| `cep` | 00000-000 |
| `telefone` | telefone do serviço |
| `horario` | dias e horário de atendimento |
| `fonte_url` | URL oficial |
| `data_verificacao` | 2026-11-05 |

### `dados/normas.csv`

| Coluna | Exemplo |
| :--- | :--- |
| `norma` | Lei 14.674/2023 |
| `esfera` | federal ou distrital |
| `tema` | juridico, beneficio ou risco |
| `artigos_relevantes` | art. 23, VI |
| `resumo` | uma frase |
| `vigencia_inicio` | data |
| `fonte_url` | URL oficial |
| `data_verificacao` | 2026-11-05 |

### Notas do Fonar
`dados/fonar/notas.md` lista as perguntas do modelo vigente (Portaria Conjunta CNJ/CNMP nº 6/2025), com a fonte, e marca para cada uma: "adaptável para autoaplicação", "adaptável com cuidado" ou "não adaptável", com o motivo.

### Benefício distrital
Escolher 1 benefício ou programa do GDF voltado a mulheres em situação de violência ou vulnerabilidade, com critérios publicados em norma. Critério de escolha: regras objetivas o suficiente para virar regra determinística na S3.

**Decisão registrada (05/11/2026):**
- **Benefício distrital escolhido para a S3:** **Aluguel Social para Mulheres Vítimas de Violência Doméstica no Distrito Federal** (`Lei Distrital nº 6.623/2020`, regulamentada pelo `Decreto Distrital nº 45.989/2024` e pela `Portaria SMDF nº 49/2026`), tendo como benefício distrital complementar de segurança alimentar o **Programa Cartão Prato Cheio** (`Lei Distrital nº 7.009/2021` e `Decreto Distrital nº 42.873/2021`, que prevê prioridade legal para mulheres vítimas de violência doméstica no DF e valor fixo de R$ 250,00).
- **Motivo da escolha:**
  1. **Regras objetivas e auditáveis em norma oficial (SINJ-DF):** possuem critérios determinísticos claros (residência no DF, inscrição no CadÚnico, teto de renda familiar per capita de até meio salário mínimo, necessidade de afastamento do lar/medida protetiva ou encaminhamento pela rede especializada do DF — Casa da Mulher Brasileira, CEAM, DEAM, Defensoria ou CREAS).
  2. **Alinhamento direto com as personas e o caso de uso:** responde diretamente à barreira de dependência financeira e habitacional para romper o ciclo da violência, complementando no plano distrital o auxílio-aluguel federal da `Lei nº 14.674/2023` (art. 23, VI da Lei Maria da Penha).
  3. **Sincronia com o RAG jurídico (`backend/config/fontes.yaml`):** os textos integrais consolidados já foram ingeridos diretamente do SINJ-DF.

### Validação
`scripts/validar_dados.py` confere colunas obrigatórias preenchidas, URLs de domínio oficial e datas válidas.

## Risks / Trade-offs

- **Informação desatualizada nos sites oficiais**: mitigação com a data de verificação exibida e a orientação de confirmar por telefone.
- **Nenhum benefício distrital com regras objetivas**: nesse caso, registrar a busca feita e seguir só com os benefícios federais (é o 3º item da ordem de corte).
- **Modelo do Fonar difícil de achar na versão de 2025**: usar o anexo da Portaria Conjunta nº 6/2025 já citado nas referências da Semana 1.
