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

### S2: Base de conhecimento e recuperação (ter 03, qui 05, sex 06/11)

**Entregável do curso:** primeiro mecanismo de RAG.
**Pronto quando:** uma pergunta jurídica é respondida com o artigo citado, e o alerta de 190 dispara por regra. A verificação na URL publicada fica para a S5, junto com o deploy.

| Mudança | Status |
| :--- | :--- |
| `s2-plataforma-base`: backend, PWA mínima com saída rápida, cliente de LLM, CI e primeiro deploy | Em andamento (8/13: backend, PWA e decisão de LGPD concluídos; deploy adiado para a S5) |
| `s2-alerta-risco-190`: regras compartilhadas PWA + backend, suíte sem falso negativo | Em andamento (6/8: faltam a medição no celular e o arquivamento) |
| `s2-rag-juridico`: Lei Maria da Penha por artigo, embeddings locais, resposta com citação e recusa | Em andamento (7/9: faltam a verificação na URL publicada, adiada para a S5, e o arquivamento) |
| `s2-fontes-df`: rede de proteção do DF, normas federais e distritais, notas do Fonar | Em andamento (5/6: falta o arquivamento) |
| `s2-base-juridica-unificada`: 16 normas na raiz com o `e5-base` em memória, filtro por eixo, remove `backend/` (Chroma) | Implementada, aguardando revisão da equipe (8/9) |

**Decisões da S2** (registradas em `s2-plataforma-base/design.md`):
- [ ] Plataforma de deploy: adiada para a S5, ainda em aberto (decisão de 09/11)
- [x] Tratamento LGPD do DeepSeek: opção (c), risco declarado com uso só de casos fictícios (decisão de 09/11)

### S3: Comparação LLM x RAG (ter 10, qui 12, sex 13/11)

**Entregável do curso:** respostas baseadas em evidências.
**Pronto quando:** o relatório comparativo mostra **precisão jurídica ≥ 90%** e **fidelidade às fontes** (100% citadas, ≤ 5% sem suporte) da versão com RAG, medidas com o modelo de produção.

| Mudança (propor na terça, 10/11) | Status |
| :--- | :--- |
| `s3-base-legal-ampliada`: Código Penal ampliado, guarda (Código Civil e CPC), correção da leitura de artigos como "1.584" e nova calibração do limite | Planejada |
| `s3-avaliacao-llm-vs-rag`: 30 perguntas com gabarito e fonte, 10 extras fora do tema, correção só por LLM externo, declarada no relatório | Planejada |
| `s3-triagem-fonar`: perguntas adaptadas do Fonar e regras de nível de urgência | Planejada |
| `s3-frontend-e-perfil`: navegação e telas do site; perfil guardado só no navegador, com função de apagar; Benefícios e Onde buscar ajuda exigem o formulário | Planejada |
| `s3-beneficios`: regras de 3 benefícios federais + 1 distrital | Planejada |

**Adiantar para a S4** (que perde a sexta por feriado): definir o contrato comum dos agentes (entrada, saída, citações) no design de `s3-beneficios`.

### S4: Sistema multiagentes (ter 17, qui 19/11; sexta 20/11 é feriado)

**Entregável do curso:** primeiro sistema multiagentes.
**Pronto quando:** **acurácia de elegibilidade ≥ 90%** e **sensibilidade para risco alto = 100%** nos casos fictícios.

| Mudança (propor na terça, 17/11) | Status |
| :--- | :--- |
| `s4-orquestrador-agentes`: orquestrador + agentes jurídico, benefícios, triagem e rede; perguntas sugeridas; modo "ajudando outra pessoa" | Planejada |
| `s4-rede-atendimento`: CNES do DF + lista curada; busca por RA ou CEP; Ligue 180 fora do DF | Planejada |

### S5: Multimodalidade (ter 24, qui 26, sex 27/11)

**Entregável do curso:** agentes multimodais.
**Pronto quando:** uma pergunta por áudio é respondida de ponta a ponta na URL publicada.

| Mudança (propor na terça, 24/11) | Status |
| :--- | :--- |
| `s5-entrada-audio`: transcrição local (ex.: Whisper), sem guardar o áudio | Planejada |
| `s5-documento-foto`: extração de texto da foto (OCR), sem guardar a imagem | Planejada |

**Deploy:** a primeira publicação passa para esta semana, e a plataforma continua em aberto (decisão de 09/11).
**Atenção:** a API do DeepSeek só aceita texto. Áudio e imagem precisam de componentes próprios, o que aumenta a memória exigida no deploy.
**Folga:** se S3 ou S4 atrasarem, esta semana absorve o atraso, seguindo a ordem de corte.

### S6: Integração completa (ter 01, qui 03, sex 04/12)

**Entregável do curso:** aplicação funcional.
**Pronto quando:** **tempo até o 190 ≤ 2 s** e **95% das respostas em até 10 s** no ambiente publicado.

| Mudança (propor na terça, 01/12) | Status |
| :--- | :--- |
| `s6-producao`: LLM de produção conforme a decisão de LGPD, deploy final, PWA instalável com nome e ícone discretos, auditoria WCAG 2.1 AA, medição de latência | Planejada |

### S7: Testes e refinamento (ter 08, qui 10, sex 11/12)

**Entregável do curso:** relatório final + apresentação.
**Pronto quando:** todas as métricas medidas, **SUS ≥ 70** e relatório com a seção de limitações.

| Mudança (propor na terça, 08/12) | Status |
| :--- | :--- |
| `s7-validacao-final`: rodar todas as métricas, corrigir falhas, SUS com colegas (terça e quinta), relatório e apresentação (sexta) | Planejada |

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

1. Leitura de documento por foto
2. Pergunta por áudio
3. Benefício distrital (ficam só os federais)
4. Perguntas sugeridas

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
