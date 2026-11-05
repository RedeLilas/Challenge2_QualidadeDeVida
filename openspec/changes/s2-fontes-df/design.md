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
Apenas fontes oficiais: portais do Governo do DF (`df.gov.br`, secretarias e `sinj.df.gov.br`), Polícia Civil do DF (`pcdf.df.gov.br`), Defensoria Pública do DF (`defensoria.df.gov.br` / `.def.br`), Poder Judiciário e CNJ (`tjdft.jus.br`, `cnj.jus.br` e demais `.jus.br`), Ministério Público (`mpdft.mp.br` e demais `.mp.br`), Poder Legislativo (`camara.leg.br`, `senado.leg.br`, `cl.df.gov.br` e demais `.leg.br`), Planalto (`planalto.gov.br`), portal `gov.br` e CNES/DATASUS. Notícias e blogs servem só como pista para achar a fonte oficial.

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
`dados/fonar/notas.md` lista as perguntas do modelo vigente (Portaria Conjunta CNJ/CNMP nº 6/2025, Anexo Único compilado pelo CNJ), com a numeração oficial (`1` a `24` e subitens `2.1`, `2.2`, `5.1`, `12.1`, `14.1`, `14.2`, `14.3` e `14.4` na Parte I, além dos itens `1` a `8` da Parte II) e a fonte, e marca para cada uma: "adaptável para autoaplicação", "adaptável com cuidado" ou "não adaptável", com o motivo.

### Benefício distrital
Escolher 1 benefício ou programa do GDF voltado a mulheres em situação de violência ou vulnerabilidade, com critérios publicados em norma. Critério de escolha: regras objetivas o suficiente para virar regra determinística na S3.

**Decisão registrada (05/11/2026):**
- **Benefício distrital escolhido para a S3 (escopo: 3 federais + 1 distrital, conforme `ROADMAP.md`):** **Aluguel Social para Mulheres Vítimas de Violência Doméstica no Distrito Federal** (`Lei Distrital nº 6.623/2020`, regulamentada pelo `Decreto Distrital nº 45.989/2024` e pela `Portaria SMDF nº 49/2026`), no valor mensal de R\$ 600,00 por até 6 meses, prorrogável uma única vez por igual período (`Decreto 45.989/2024, art. 3º`; `Portaria SMDF 49/2026, arts. 4º e 21`).
- **Critérios objetivos de elegibilidade na norma vigente (`Portaria SMDF nº 49/2026, art. 5º c/c art. 2º, I`):**
  1. **Medida Protetiva de Urgência (MPU) vigente:** possuir MPU vigente expedida no Distrito Federal com base na Lei nº 11.340/2006 (`art. 5º, I`; observando-se que o `art. 1º, § 2º` da `Lei Distrital 6.623/2020`, incluído pela `Lei 7.879/2026`, prevê o acesso desde o registro do boletim de ocorrência policial);
  2. **Acompanhamento psicossocial:** estar em acompanhamento psicossocial em equipamento da Secretaria de Estado da Mulher (SMDF) ou da Rede de Proteção à Mulher Vítima de Violência (`art. 5º, II`);
  3. **Residência:** residir no Distrito Federal (`art. 5º, III`);
  4. **Vulnerabilidade socioeconômica e habitacional:** apresentar **renda per capita mensal de até meio salário mínimo ou renda familiar mensal total de até dois salários mínimos**, não dispondo de condições financeiras para arcar com despesas de moradia sem prejuízo do sustento básico (`art. 2º, I`), e necessitar de saída emergencial do lar (`art. 5º, IV, a`) ou de permanência no imóvel alugado em que reside (`art. 5º, IV, b`).
  - *Observação importante para a regra da S3:* a inscrição no Cadastro Único (**CadÚnico**) e no programa habitacional da **CODHAB** **não é requisito prévio de concessão**, mas sim obrigação da beneficiária **durante o acompanhamento** (`Portaria SMDF nº 49/2026, art. 15, III e IV`: *"realizar inscrição no Cadastro Único da Assistência Social – CADÚNICO, caso não o possua"*).
- **Motivo da escolha (e descarte dos demais benefícios distritais como regra principal da S3):**
  1. **Regras determinísticas específicas para violência doméstica:** o Aluguel Social é o único benefício distrital desenhado especificamente para mulheres vítimas de violência doméstica no DF, com critérios objetivos expressos nos `arts. 2º e 5º` da `Portaria SMDF nº 49/2026`.
  2. **Por que o Cartão Prato Cheio (`Lei Distrital 7.009/2021` e `Decreto 42.873/2021`) não foi escolhido como o benefício distrital da S3:** as normas do Prato Cheio não trazem recorte específico para violência doméstica (priorizam famílias monoparentais chefiadas por mulheres com crianças de 0 a 6 anos, conforme `art. 2º, § 2º, II` do `Decreto 42.873/2021`, alterado pelo `Decreto 48.095/2025`), além de as normas distritais de segurança alimentar e benefícios eventuais (`Lei 5.165/2013`, `Lei 6.938/2021`, `Lei 7.009/2021`) continuarem disponíveis na base jurídica (`dados/leis/`) para orientação geral no RAG.
  3. **Sincronia com o RAG jurídico (`dados/fontes/fontes.yaml`):** os textos integrais da `Lei Distrital 6.623/2020`, do `Decreto 45.989/2024` e da `Portaria SMDF 49/2026` já estão coletados em `dados/leis/`.

### Validação
`scripts/validar_dados.py` confere colunas obrigatórias preenchidas, URLs de domínio oficial, datas válidas, CEPs na faixa do DF (`70000-000` a `73699-999`), Regiões Administrativas oficiais do DF, ausência de linhas duplicadas, sincronia com `dados/fontes/fontes.yaml` e a numeração oficial do Fonar 2025.

## Risks / Trade-offs

- **Informação desatualizada ou certificado intermediário ausente em sites oficiais**: páginas de secretarias do GDF (como `mulher.df.gov.br`) podem apresentar erro de cadeia de certificado SSL em clientes sem a cadeia ICP-Brasil instalada, e buscadores dinâmicos com reCAPTCHA (`rh.tjdft.jus.br/enderecos`) impedem consulta direta; mitigação usando páginas estáticas/APIs oficiais verificadas (`pcdf.df.gov.br`, `rededeprotecao.tjdft.jus.br`, `tjdft.jus.br`, `defensoria.df.gov.br`, `mulher.df.gov.br`), exibindo a data de verificação e orientando a confirmar por telefone.
- **Nenhum benefício distrital com regras objetivas**: mitigado pela publicação da `Portaria SMDF nº 49/2026`, que detalhou os requisitos objetivos do Aluguel Social.
- **Modelo do Fonar na versão de 2025**: utilizado o Anexo Único compilado pelo CNJ (`compilado190716202508066893a7e440efa.pdf`) vinculado à `Portaria Conjunta CNJ/CNMP nº 6/2025`.
