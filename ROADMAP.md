# Rede Lilás: Roadmap do Challenge 2

Guia de desenvolvimento da equipe (Ana Beatriz, Léo Alec, Rafaella Borges, Túlio Celeri e Vítor Gonçalves). Este arquivo diz **o que fazer em cada semana**. **O que o sistema deve fazer** está em `openspec/specs/`, e **como cada entrega é feita** está em `openspec/changes/<mudança>/`.

- **Escopo:** Distrito Federal. Legislação federal (Lei Maria da Penha, Fonar, benefícios federais) + normas distritais. Rede de serviços apenas do DF.
- **Stack:** Python (FastAPI) + PWA; LLM local nos testes, DeepSeek em produção; deploy desde a S2.
- **Validação:** sem entrevistas nem usuárias reais. Casos fictícios, gabarito da equipe com fonte, LLM juiz + revisão em dupla de 20%, SUS com colegas.
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
4. A versão com a mudança está publicada na URL de teste (a partir da S2).
5. A mudança foi arquivada.

---

## Plano semana a semana

### S1: Problema, stakeholders, riscos e métricas (26–30/10) ✅

| Mudança | Status |
| :--- | :--- |
| Definições do projeto (`docs/Challenge 2 - Definições do Projeto Semana 1.md`) | Entregue |
| `s1-definicoes-base`: definições convertidas em 9 specs | Aguardando revisão da equipe |

### S2: Base de conhecimento e recuperação (ter 03, qui 05, sex 06/11)

**Entregável do curso:** primeiro mecanismo de RAG.
**Pronto quando:** uma pergunta jurídica é respondida com o artigo citado na URL publicada, e o alerta de 190 dispara por regra.

| Mudança | Status |
| :--- | :--- |
| `s2-plataforma-base`: backend, PWA mínima com saída rápida, cliente de LLM, CI e primeiro deploy | Proposta |
| `s2-alerta-risco-190`: regras compartilhadas PWA + backend, suíte sem falso negativo | Proposta |
| `s2-rag-juridico`: Lei Maria da Penha por artigo, embeddings locais, resposta com citação e recusa | Em andamento (4/9: ingestão, índice e teste rápido) |
| `s2-fontes-df`: rede de proteção do DF, normas federais e distritais, notas do Fonar | Em andamento (5/6: levantamento, escolha do benefício distrital e validação concluídos) |
| `s2-base-juridica-unificada`: 16 normas na raiz com o `e5-base` em memória, filtro por eixo, remove `backend/` (Chroma) | Implementada, aguardando revisão da equipe (8/9) |

**Decisões até sexta, 06/11** (registrar em `s2-plataforma-base/design.md`):
- [ ] Plataforma de deploy (recomendação: Hugging Face Spaces com Docker)
- [ ] Tratamento LGPD do DeepSeek: (a) anonimizar antes do envio, (b) pesos abertos em outro provedor ou (c) risco declarado com uso só de casos fictícios

### S3: Comparação LLM x RAG (ter 10, qui 12, sex 13/11)

**Entregável do curso:** respostas baseadas em evidências.
**Pronto quando:** o relatório comparativo mostra **precisão jurídica ≥ 90%** e **fidelidade às fontes** (100% citadas, ≤ 5% sem suporte) da versão com RAG, medidas com o modelo de produção.

| Mudança (propor na terça, 10/11) | Status |
| :--- | :--- |
| `s3-avaliacao-llm-vs-rag`: 50 perguntas com gabarito e fonte, LLM juiz, revisão em dupla de 20% | Planejada |
| `s3-triagem-fonar`: perguntas adaptadas do Fonar e regras de nível de urgência | Planejada |
| `s3-beneficios-e-perfil`: regras de 3 benefícios federais + 1 distrital; perfil opcional no aparelho | Planejada |

**Adiantar para a S4** (que perde a sexta por feriado): definir o contrato comum dos agentes (entrada, saída, citações) no design de `s3-beneficios-e-perfil`.

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
