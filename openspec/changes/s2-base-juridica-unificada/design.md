# Design

## Context

Estado em 04/11:

| | Raiz (`app/rag/`) | `backend/` |
|---|---|---|
| Normas | Lei 11.340/2006 | 16 (federais do Planalto, distritais do SINJ-DF) |
| Divisão | até 1500 caracteres por artigo (109 trechos) | um registro por dispositivo (1.167 vigentes) |
| Embeddings | `multilingual-e5-base` em processo (`sentence-transformers`) | `bge-m3` via servidor Ollama |
| Índice | matriz em memória | Chroma em disco |
| Versionamento | diff do git em `dados/leis/` | HTML bruto, dispositivos por data e relatório de alterações |
| Testes | 10 (pytest) | nenhum |

Os dois leitores de HTML (`planalto.py`) são quase idênticos, mas cada um tem uma correção que falta no outro.

## Goals / Non-Goals

**Goals:**
- Uma única base jurídica, com a coleta das 16 normas e o índice decidido em `s2-rag-juridico`.
- Manter a meta do teste rápido (artigo esperado no top 5 em pelo menos 9 de 10) para a orientação jurídica.
- Remover `backend/`, sem perder histórico nem dados coletados.

**Non-Goals:**
- Banco vetorial externo.
- Novas normas além das 16 já coletadas.
- Escolher o eixo automaticamente a partir da pergunta (fica com o orquestrador da S4).
- Índice pré-calculado em arquivo.

## Decisions

### Embeddings: manter o `multilingual-e5-base` em memória
Medições de 04/11, top 5 nas 10 perguntas do teste rápido:

| Base | e5-base | e5-large | bge-m3 (Ollama) |
|---|---|---|---|
| Lei Maria da Penha, 109 trechos agrupados | 10 | 10 | — |
| Lei Maria da Penha, um trecho por dispositivo | 9 | 10 | 7 |
| 16 normas, um trecho por dispositivo | 6 | 8 | 6 |
| 16 normas, trechos agrupados | 7 | — | — |
| Eixo jurídico (11.340 + 14.149 + Código Penal), agrupados | 9 | — | — |

Custo medido em CPU: `e5-base` +1,4 GB de memória e 8 ms por pergunta; `e5-large` +2,4 GB e 27 ms; `bge-m3` cerca de 1,2 GB, mais um serviço separado.

- Alternativa descartada: `bge-m3` via Ollama. Não supera o `e5-base` em nenhum cenário e obriga o deploy a rodar o Ollama ao lado da API, contra o container único da stack.
- Alternativa adiada: `multilingual-e5-large`. É melhor com as 16 normas (8 contra 6), mas usa cerca de 1 GB a mais. Fica como opção se o filtro por eixo não bastar na avaliação da S3.
- Alternativa descartada: Chroma. Com cerca de 558 trechos, a matriz em memória responde em milissegundos (Non-Goal já registrado em `s2-rag-juridico`).

### Divisão: a mesma de `s2-rag-juridico`
Até 1500 caracteres por artigo; artigos maiores são divididos pelos filhos diretos do caput, repetindo o caput. Com as 16 normas, a divisão agrupada rendeu 7 de 10, contra 6 com um trecho por dispositivo.

### Filtro por eixo
Com as 16 normas sem filtro, artigos de benefícios disputam o top 5 em perguntas jurídicas ("controla meu dinheiro" recupera LOAS e Bolsa Família). Cada norma de `fontes.yaml` ganha um `eixo` (`juridico`, `beneficios`, `saude`, `df`), copiado para os trechos, e `Indice.buscar()` aceita `eixos` opcional. A rota jurídica busca com `eixos={"juridico"}` (9 de 10). Sem filtro, a busca cobre toda a base.
- Alternativa considerada: um índice por eixo. Descartada: o filtro sobre a mesma matriz é mais simples e permite combinar eixos.

### Estrutura de pastas

```
app/rag/
  planalto.py     # leitor de HTML do Planalto e do SINJ-DF
  versoes.py      # raw, dispositivos por data, comparação e relatório
  coleta.py       # baixa (ou reprocessa) as normas -> dispositivos + relatório
  ingestao.py     # dispositivos -> trechos em dados/leis/
  indice.py       # e5-base em memória, filtro por eixo
  buscar.py       # consulta manual pelo terminal
dados/
  fontes/
    fontes.yaml
    raw/<norma_id>/<data>_<hash>.html
    dispositivos/<norma_id>/<data>.jsonl
    relatorios/<data>.md
  leis/<norma_id>.jsonl
```

`dados/fontes/` guarda a coleta (rastreabilidade e diff entre datas); `dados/leis/` guarda só o que alimenta o índice. Os arquivos do `backend/` são movidos com `git mv` para manter o histórico.
- Alternativa considerada: `config/fontes.yaml` na raiz. Descartada para não criar uma pasta fora da estrutura de `s2-plataforma-base`; a lista de normas fica junto dos dados que gera.

### Leitor de HTML unificado
- Do `backend/`: `(?!\w)` em `RE_ARTIGO` e `RE_PARAGRAFO` (sem ele, "Art. 147 - Ameaçar" vira art. 147-A) e a propriedade `hash` do dispositivo.
- Da raiz: `RE_VETADO` aceita "(VETADO." sem o parêntese de fechamento.
- Os HTMLs já salvos são reprocessados com o leitor unificado (`coleta.py --reprocessar`), sem baixar de novo, e o relatório mostra o que mudou.

### Formato dos trechos
Mantém os campos de `s2-rag-juridico` (`lei`, `artigo`, `inciso`, `paragrafo`, `citacao`, `texto`, `titulo`, `capitulo`, `secao`, `notas`, `url`, `data_acesso`) e acrescenta `norma_id` e `eixo`. O `id` passa a ser `<norma_id>:<id do dispositivo>`. `data_acesso` é a data da coleta usada.

## Risks / Trade-offs

- **Meta do teste rápido no limite**: o eixo jurídico dá 9 de 10, exatamente a meta. Uma pergunta nova que falhe derruba o teste. Mitigação: se cair, registrar e comparar com o `e5-large` antes de mudar a meta.
- **Gabarito restrito à Lei Maria da Penha**: parte dos "erros" com as 16 normas é resposta pertinente de outra norma (ex.: auxílio-aluguel → Lei Distrital 6.623/2020). A S3 deve aceitar mais de uma norma no gabarito.
- **Reprocessamento muda dispositivos**: o leitor unificado pode alterar textos com "(VETADO.". Mitigação: revisar o relatório antes de gravar.
- **Inicialização mais lenta**: cerca de 20 s para indexar 558 trechos em CPU. Aceitável agora; o índice pré-calculado fica para quando a base crescer.
- **Trabalho de outra pessoa removido**: o `backend/` foi implementado em 03/11. A remoção deve ser combinada com a equipe antes do merge.
