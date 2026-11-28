# Rede Lilás: Roadmap do Challenge 2

Guia de desenvolvimento da equipe (Ana Beatriz, Léo Alec, Rafaella Borges, Túlio Celeri e Vítor Gonçalves). Este arquivo diz **o que fazer em cada semana**. **O que o sistema deve fazer** está em `openspec/specs/`, e **como cada entrega é feita** está em `openspec/changes/<mudança>/`.

- **Escopo:** Distrito Federal. Legislação federal (Lei Maria da Penha, Fonar, benefícios federais) + normas distritais. Rede de serviços apenas do DF.
- **Stack:** Python (FastAPI) + PWA; LLM local nos testes, DeepSeek em produção; deploy na S5.
- **Validação:** sem entrevistas nem usuárias reais. Casos fictícios, gabarito da equipe com fonte, correção só por LLM externo (declarada no relatório), SUS com colegas.
- **Dias de trabalho:** terça, quinta e sexta.

---

## Como usar o OpenSpec

Instalação (uma vez por máquina, sem `sudo`):

```bash
curl -fsSL https://openspec.dev/cli/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"   # adicionar também ao ~/.zshrc
```

| Quando | Comando no Claude Code | O que faz |
| :--- | :--- | :--- |
| Antes de decidir algo | `/opsx:explore` | Conversa para explorar opções sem gerar arquivos |
| Terça, início da semana | `/opsx:propose s3-nome-da-mudanca` | Cria proposta, design, specs e tarefas da mudança |
| Durante a semana | `/opsx:apply` | Implementa as tarefas da mudança |
| Plano mudou | `/opsx:update` | Ajusta os artefatos da mudança |
| Mudança concluída | `/opsx:archive` | Move para `archive/` e atualiza `openspec/specs/` |

Comandos úteis no terminal: `openspec list`, `openspec view`, `openspec validate --all`, `openspec show <mudança>`.

---

## Rotina semanal

- **Terça, começo do dia (30 min):** revisar o status, rodar `/opsx:propose` para as mudanças da semana (lista abaixo), distribuir as tarefas entre as pessoas.
- **Terça, quinta e sexta:** cada tarefa cabe em um dia e termina com um teste ou verificação objetiva.
- **Sexta, fim do dia:** arquivar as mudanças concluídas, atualizar a coluna **Status** abaixo e fazer a entrega do curso.

### Uma mudança está pronta quando

1. Todas as tarefas do `tasks.md` estão marcadas.
2. Os testes passam, **incluindo a suíte de risco/190**.
3. `openspec validate <mudança>` passa.
4. A versão com a mudança está publicada na URL de teste (a partir da S5).
5. A mudança foi arquivada.

---

## Plano semana a semana

### S1: Problema, stakeholders, riscos e métricas (26–30/10) ✅

| Mudança | Status |
| :--- | :--- |
| Definições do projeto (`docs/Challenge 2 - Definições do Projeto Semana 1.md`) | Entregue |
| `s1-definicoes-base`: definições convertidas em 9 specs | Arquivada em 10/11 (a tarefa 2.1, leitura das specs pela equipe, não foi feita) |

### S2: Base de conhecimento e recuperação (ter 03, qui 05, sex 06/11) ✅

**Entregável do curso:** primeiro mecanismo de RAG.
**Pronto quando:** uma pergunta jurídica é respondida com o artigo citado, e o alerta de 190 dispara por regra. A verificação na URL publicada fica para a S5, junto com o deploy.

| Mudança | Status |
| :--- | :--- |
| `s2-plataforma-base`: backend, PWA mínima com saída rápida, cliente de LLM, CI e primeiro deploy | Arquivada em 24/11 (backend, PWA e decisão de LGPD concluídos; Dockerfile, CI, publicação e decisão da plataforma (3.1, 3.2, 3.3 e 4.1) movidos para a `s5-deploy`) |
| `s2-alerta-risco-190`: regras compartilhadas PWA + backend, suíte sem falso negativo | Arquivada em 24/11 (medição no celular do tempo até o alerta (2.3) movida para a `s6-producao`) |
| `s2-rag-juridico`: Lei Maria da Penha por artigo, embeddings locais, resposta com citação e recusa | Arquivada em 24/11 (verificação na URL publicada (2.4) movida para a `s5-deploy`) |
| `s2-fontes-df`: rede de proteção do DF, normas federais e distritais, notas do Fonar | Arquivada em 24/11 (6/6) |
| `s2-base-juridica-unificada`: 16 normas na raiz com o `e5-base` em memória, filtro por eixo, remove `backend/` (Chroma) | Arquivada em 24/11 (9/9; revisão da equipe feita, suíte de risco/190 passando) |

**Decisões da S2** (registradas em `archive/2026-11-24-s2-plataforma-base/design.md`):
- [x] Plataforma de deploy: adiada para a S5 (decisão de 09/11) e decidida em 24/11 na `s5-deploy`: Azure App Service Linux B3 em brazilsouth, com Docker
- [x] Tratamento LGPD do DeepSeek: opção (c), risco declarado com uso só de casos fictícios (decisão de 09/11)

### S3: Comparação LLM x RAG (ter 10, qui 12, sex 13/11)

**Entregável do curso:** respostas baseadas em evidências.
**Pronto quando:** o relatório comparativo mostra **precisão jurídica ≥ 90%** e **fidelidade às fontes** (100% citadas, ≤ 5% sem suporte) da versão com RAG, medidas com o modelo de produção.

| Mudança (propor na terça, 10/11) | Status |
| :--- | :--- |
| `s3-base-legal-ampliada`: Código Penal ampliado, guarda (Código Civil e CPC), correção da leitura de artigos como "1.584" e nova calibração do limite | Arquivada em 15/11 (10/10; limite mantido em 0,81) |
| `s3-avaliacao-llm-vs-rag`: 30 perguntas com gabarito e fonte, 10 extras fora do tema, correção só por LLM externo, declarada no relatório | Arquivada em 15/11 (19/19; relatório em `docs/Relatório S3 - Comparação LLM x RAG.md`) |
| `s3-triagem-fonar`: perguntas adaptadas do Fonar e regras de nível de urgência | Arquivada em 15/11 (8/8) |
| `s3-frontend-e-perfil`: navegação e telas do site; perfil guardado só no navegador, com função de apagar; Benefícios e Onde buscar ajuda exigem o formulário | Arquivada em 15/11 (12/12) |
| `s3-beneficios`: regras de 3 benefícios federais + 1 distrital | Arquivada em 15/11 (7/7) |

**Resultado (rodada oficial de 15/11, versão com RAG):** precisão de 16/30 (53,3%), abaixo da meta de 90%; 3,9% das afirmações sem suporte, dentro da meta de 5%; 27/30 respostas citadas, abaixo de 100% (as 3 sem citação são recusas do sistema). A S3 foi fechada com a meta de precisão não atingida (ver registro de decisões de 15/11).

**Adiantar para a S4** (que perde a sexta por feriado): definir o contrato comum dos agentes (entrada, saída, citações) no design de `s3-beneficios`.

### S4: Sistema multiagentes (ter 17, qui 19/11; sexta 20/11 é feriado) ✅

**Entregável do curso:** primeiro sistema multiagentes.
**Pronto quando:** **acurácia de elegibilidade ≥ 90%** e **sensibilidade para risco alto = 100%** nos casos fictícios.

| Mudança (propor na terça, 17/11) | Status |
| :--- | :--- |
| `s4-orquestrador-agentes`: rota `/orquestrar` (regra + LLM), agentes jurídico, benefícios, triagem e rede, várias perguntas, "Continuar" depois do alerta de 190, modo "ajudando outra pessoa"; casos fictícios e medição das duas metas | Concluída em 19/11 (27/27); arquivada em 24/11 |
| `s4-rede-atendimento`: CEP → RA por tabela local no navegador, CRAS da Sedes-DF, saúde de referência (SES-DF + CNES); Ligue 180 fora do DF | Concluída em 19/11 (15/15); arquivada em 24/11 |
| `s4-rag-beneficios`: RAG só para explicar benefícios (eixos `beneficios` e `df`), apelidos das normas na verificação de citação, limite próprio | Concluída em 19/11 (11/11): testada, não medida; arquivada em 24/11 |

**Ordem de corte da S4:** 1) `s4-rag-beneficios` inteira (vai para a S6); 2) refinamento das perguntas sugeridas; 3) serviços de saúde do CNES. **Nunca cortar:** alerta de 190, saída rápida, ausência de histórico, citação de fontes e a medição das duas metas da S4.

### S5: Multimodalidade (ter 24 e qui 26/11; só 2 dias de trabalho)

**Entregável do curso:** agentes multimodais.
**Pronto quando:** uma pergunta por áudio é respondida de ponta a ponta (decisão de 24/11: não exige a URL publicada).
**Só texto e áudio:** sem fotos. A `s5-documento-foto` saiu do plano, e o requisito "Leitura de documento fotografado" sai da spec `conversa` com a `s5-entrada-audio` (decisão de 24/11).

| Mudança (proposta na terça, 24/11) | Status |
| :--- | :--- |
| `s5-entrada-audio` (terça): botão de microfone, transcrição com Whisper (faster-whisper `small`, int8) no servidor da aplicação, sem serviço externo e sem guardar o áudio; regra de risco sobre o texto transcrito no navegador; transcrição na caixa para conferir; limites de 30 s e 1 MB; medição da memória com o RAG | Arquivada em 27/11 (12/12; publicada na URL de teste com a `s5-deploy`) |
| `s5-deploy` (quinta): decisão da plataforma e do Docker (primeira tarefa), torch só para CPU, modelos no build, vetores no build se couber, CI, publicação e verificação na URL; recebe as pendências de deploy da S2 | Arquivada em 27/11 (9/9). Plataforma decidida em 24/11: Azure App Service Linux B3 em brazilsouth, com Docker. Publicada em 24/11 em https://rede-lilas.azurewebsites.net; partida a frio e memória medidas em 25/11; suíte inteira e `openspec validate --all` passando em 25/11. Roteiro na URL verificado num iPhone 13 e num Android em 25/11 (3.3) |

**Antes da quinta:** memória medida (`s5-entrada-audio` 5.1), aprovação de gasto, dono da conta e do cartão e acessos (lista no design da `s5-deploy`). Em 24/11, nenhuma plataforma que caiba na memória (~3,1 GB estimados) é gratuita sem cartão; o HF Spaces exige o PRO (US$ 9/mês) para Spaces Docker.
**Atenção:** a API do DeepSeek só aceita texto. O áudio precisa do Whisper no servidor, o que aumenta a memória exigida no deploy.

**Ordem de corte da S5** (a semana tem 2 dias, e o deploy depende de conta e gasto aprovados):
1. Workflow de CI (vai para a S6)
2. Vetores gerados no build (vão para a S6; a partida a frio fica mais longa)
3. `Dockerfile`, se a plataforma escolhida for sem Docker (vai para a S6)
4. Gravações reais no iPhone (ficam os casos do Android e a voz sintética)
5. Publicação na URL (vai para a `s6-producao`; a semana fecha pelo critério de pronto, e as duas mudanças ficam abertas)
6. Pergunta por áudio inteira (último corte: é o entregável da semana; vai para a S6)

**Nunca cortar:** alerta de 190, saída rápida, ausência de histórico e citação de fontes. Se o áudio entrar, entra sem guardar o arquivo e sem nada nos logs.
**Cabe na semana?** O áudio cabe na terça se a equipe dividir as frentes (servidor, navegador, casos e medição). O deploy na quinta cabe só se a aprovação de gasto e a conta estiverem prontas antes; sem isso, a publicação vai para a S6 (item 5).

### S6: Integração completa (ter 01, qui 03, sex 04/12)

**Entregável do curso:** aplicação funcional.
**Pronto quando:** **tempo até o 190 ≤ 2 s** e **95% das respostas em até 10 s** no ambiente publicado.

| Mudança (propor na terça, 01/12) | Status |
| :--- | :--- |
| `s6-producao`: LLM de produção conforme a decisão de LGPD, deploy final, PWA instalável com nome e ícone discretos, auditoria WCAG 2.1 AA, medição de latência; medição no celular do tempo até o alerta de 190 (≤ 2 s; vem de `s2-alerta-risco-190` 2.3, e no áudio conta a partir da chegada da transcrição) | Planejada |

### S7: Testes e refinamento (ter 08, qui 10, sex 11/12)

**Entregável do curso:** relatório final + apresentação.
**Pronto quando:** todas as métricas medidas, **SUS ≥ 70** e relatório com a seção de limitações.

| Mudança (propor na terça, 08/12) | Status |
| :--- | :--- |
| `s7-validacao-final`: rodar todas as métricas, corrigir falhas, SUS com colegas (terça e quinta), relatório e apresentação (sexta) | Planejada |

**Pendência da S3:** melhorar a recuperação do RAG (5 das 30 perguntas oficiais sem o artigo aceito no top 5, 4 delas de "isso é crime?") e refazer a rodada oficial de precisão, declarada como refeita no relatório.

---

## Métricas

| Métrica | Meta | Medida em |
| :--- | :--- | :--- |
| Precisão jurídica | ≥ 90% corretas | S3 |
| Fidelidade às fontes | 100% citadas; ≤ 5% sem suporte | S3 |
| Acurácia de elegibilidade | ≥ 90% | S4 |
| Sensibilidade para risco alto | 100% (nenhum falso negativo) | S2 (190), S4 (triagem) |
| Tempo até o 190 | ≤ 2 s | S6 |
| Tempo de resposta | p95 ≤ 10 s | S6 |
| Usabilidade (SUS com colegas) | ≥ 70 | S7 |

## Ordem de corte se atrasar

Cada semana tem a própria ordem na sua seção (S4 e S5). No projeto:

1. Pergunta por áudio
2. Benefício distrital (ficam só os federais)
3. Perguntas sugeridas

A leitura de documento por foto saiu do projeto em 24/11.

**Nunca cortar:** alerta de 190, saída rápida, ausência de histórico e citação de fontes.

## Registro de decisões

| Data | Decisão |
| :--- | :--- |
| 03/11 | Escopo: DF, com legislação federal + normas distritais |
| 03/11 | Sem entrevistas; validação com casos fictícios, LLM juiz + revisão em dupla; SUS com colegas |
| 03/11 | Stack: Python (FastAPI) + PWA; Ollama nos testes e DeepSeek em produção; deploy desde a S2 |
| 03/11 | OpenSpec com CLI + Claude Code; tarefas distribuídas a cada semana, sem donos fixos |
| 09/11 | LGPD: opção (c), API oficial do DeepSeek só com casos fictícios e risco declarado no relatório |
| 09/11 | Modelo de produção e da comparação LLM x RAG: `deepseek-flash`, sem raciocínio; cada rodada registra nome, data e versão do changelog |
| 09/11 | Deploy adiado para a S5, com a plataforma em aberto; critério 4 de pronto vale a partir da S5 |
| 09/11 | Base legal ampliada antes das perguntas (Código Penal e guarda); limite de similaridade recalibrado só com as perguntas de desenvolvimento |
| 09/11 | Avaliação da S3: 30 perguntas com gabarito e fonte e 10 extras fora do tema, relatadas à parte; meta de 27 em 30 e fidelidade com 100% citadas e até 5% sem suporte; perguntas e gabaritos escritos e conferidos pela equipe |
| 09/11 | Correção por um único LLM externo, de outra empresa que não o DeepSeek, sem revisão humana das notas, com essa limitação declarada no relatório |
| 09/11 | Triagem sem pontuação, só no navegador, em três níveis e com o resultado "não foi possível descartar risco alto"; a usuária nunca vê "risco baixo" |
| 09/11 | Benefícios com regras versionadas, só no navegador, e quarto resultado "faltam informações"; lista de CRAS fica para a S4 |
| 10/11 | Perfil entra na S3: formulário que inclui idade e estado civil, guardado só no navegador, sem banco de dados, com função para apagar os dados rapidamente |
| 10/11 | O chatbot funciona sem o formulário; Benefícios e Onde buscar ajuda exigem o preenchimento |
| 10/11 | Nova mudança de front-end na S3 |
| 10/11 | `s1-definicoes-base` arquivada; a S3 altera as specs só nos pontos em conflito |
| 10/11 | A S3 mantém base legal com guarda, avaliação, triagem, front-end com perfil e benefícios, com cerca de 19 horas extras do grupo até quinta de manhã |
| 12/11 | Método da avaliação (#9): 30 perguntas oficiais e 10 extras, correção por um único LLM externo, sem a revisão em dupla prevista em 03/11 |
| 15/11 | Corretor da avaliação: Gemini 4 Argon (Google), com busca na web e memória desligadas |
| 15/11 | Limite de similaridade mantido em 0,81 depois da recalibração com as perguntas de desenvolvimento (#22) |
| 15/11 | S3 fechada com a meta de precisão não atingida (16/30 com RAG; meta de 27/30). O resultado real fica no relatório, sem ajuste na rodada oficial. A melhoria da recuperação, sobretudo dos artigos do Código Penal ("isso é crime?"), fica para a S7; uma nova rodada oficial terá de ser declarada como refeita |
| 17/11 | S4 com três mudanças: `s4-orquestrador-agentes`, `s4-rede-atendimento` e `s4-rag-beneficios`, esta a primeira a cortar |
| 17/11 | Orquestrador no servidor (`/orquestrar`): regra por palavras-chave e, na dúvida, LLM com lista fechada; reserva no jurídico. Benefícios, triagem e rede continuam no navegador, e o perfil nunca sai do aparelho |
| 17/11 | Alerta de 190 com "Continuar com minha pergunta": texto com sinal de risco só vai ao servidor depois do toque, e o 190 continua visível acima da resposta |
| 17/11 | CEP convertido em RA só no navegador, por tabela montada à mão com a Busca Faixa de CEP dos Correios; CEP digitado no chat é retirado antes do envio |
| 17/11 | CRAS pela página de unidades da Sedes-DF; saúde de referência pelos nomes da SES-DF, com endereço do CNES; urgência de violência sexual no pronto-socorro de hospital público (Lei 12.845/2013) |
| 17/11 | Medição da S4 por regra, com casos escritos com o Claude e conferidos por uma pessoa que não os escreveu; RAG de benefícios testado, não medido, sem corretor externo |
| 19/11 | Elegibilidade 79/80 (98,75%) antes da correção #110 e 80/80 (100%) depois; risco alto 38/38 (100%); roteamento: 28/30 em 17/11 e 29/30 e 28/30 em duas rodadas de 19/11; RAG testado, não medido |
| 19/11 | Teste manual da S4: "direito" só para os 4 benefícios com regra ou com marca de "tenho direito?"; respostas da conversa (jurídico e benefícios) com até 5 frases curtas; o `/juridico` da S3 não muda |
| 24/11 | S2 e S4 arquivadas. Pendências de deploy da S2 (Dockerfile, CI, publicação, decisão da plataforma e verificação na URL) vão para a `s5-deploy`; a medição no celular do tempo até o alerta vai para a `s6-producao` |
| 24/11 | S5 com só 2 dias de trabalho (terça 24/11 e quinta 26/11) e só texto e áudio, sem fotos: a `s5-documento-foto` sai do plano, e o requisito "Leitura de documento fotografado" é removido da spec `conversa` |
| 24/11 | Mudanças da S5: `s5-entrada-audio` (terça) e `s5-deploy` (quinta). Pronto quando uma pergunta por áudio é respondida de ponta a ponta, sem exigir a URL publicada |
| 24/11 | Transcrição com Whisper no servidor da aplicação (faster-whisper, `small` em int8, `base` de reserva por variável de ambiente), sem serviço externo e sem guardar o áudio. Descartados: Web Speech API (envia a voz ao Google ou à Apple) e Whisper no navegador |
| 24/11 | Exceção à decisão de 17/11: o áudio vai ao servidor antes da regra de risco, porque a regra precisa de texto. O servidor só transcreve (sem regra, sem LLM, sem guardar, sem log); a regra roda no navegador assim que a transcrição chega, e o texto com risco só vai ao orquestrador depois do "Continuar". No áudio, os ≤ 2 s até o 190 contam a partir da chegada da transcrição |
| 24/11 | Transcrição colocada na caixa de texto para a usuária conferir antes de enviar; limites de 30 s e 1 MB |
| 24/11 | Casos de áudio fictícios em `tests/audios/`, lidos por membros da equipe que concordaram ou gerados por voz sintética; nenhuma voz ou relato real |
| 24/11 | Plataforma de deploy e uso de Docker: decisão na quinta (26/11), como primeira tarefa da `s5-deploy`. Achado de 09/11 conferido: Spaces Docker no HF exigem o PRO (US$ 9/mês) |
| 24/11 | Plataforma decidida antes de quinta (#120, #131): Azure App Service Linux B3 em brazilsouth, com Docker, pago pelo crédito do Azure for Students; plano B: HF Spaces com PRO, com a mesma imagem. Revisável. Imagem no Azure Container Registry Basic, puxada por identidade gerenciada; sem logs HTTP nem da aplicação |
| 25/11 | Partida a frio no Azure: do container iniciado, `/saude` em 6,1 s, Whisper em ~14 s e índice (vetores do build) em ~38 s; 1,4 a 1,6 GB em uso de 7 GB. Publicar com uma mudança de configuração por vez |
