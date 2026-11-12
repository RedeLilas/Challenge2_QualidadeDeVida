# Design

## Context

O cliente em `app/llm.py` não envia `extra_body`, e `app/config.py` lê apenas quatro variáveis. As instruções da versão com RAG estão em `INSTRUCOES` (`app/rag/resposta.py`). Só 10 das 15 perguntas de desenvolvimento estão versionadas (`tests/perguntas_juridicas.yaml`), e as 10 fora do tema não estão no repositório. O LLM externo ainda não foi escolhido. Nenhuma rodada com o DeepSeek foi feita, e o envio de 30 respostas de uma vez não foi testado.

## Goals / Non-Goals

**Goals:**
- Tornar a rodada e a correção reproduzíveis e auditáveis.
- Impedir que o conjunto oficial mude sem registro depois do resultado.

**Non-Goals:**
- Automatizar o envio ao LLM externo. Os quatro envios são feitos manualmente, na interface dele.
- Medir latência (S6).

## Decisions

### Raciocínio controlado por variável opcional
`LLM_THINKING` é opcional. Com o valor `disabled`, o cliente envia `extra_body={"thinking": {"type": "disabled"}}`. Sem a variável, nada muda para o Ollama. Alternativa descartada: enviar sempre o parâmetro, porque ele é específico do DeepSeek e o modelo local não deve depender dele.

### Pasta `avaliacao/` versionada
- `avaliacao/conjuntos/`: `desenvolvimento.yaml` e `oficial.yaml`, escritos pela equipe.
- `avaliacao/rubricas/`: textos das correções de precisão e de fidelidade.
- `avaliacao/rodadas/<data>-<id>/`: respostas, arquivos enviados, retornos, modelo e data.

O mapa de versões fica em um arquivo separado da rodada, que nunca é enviado ao corretor. Só há casos fictícios, então tudo pode ser versionado.

### Congelamento por hash
O congelamento grava o SHA-256 de `oficial.yaml`. A rodada oficial compara o hash e recusa executar se ele divergir. Alternativa descartada: congelar apenas por combinação da equipe, que não deixa evidência.

### Estrutura YAML v1
Os dois arquivos compartilham a mesma raiz. O conjunto de desenvolvimento terá 15 itens em `perguntas` e 10 em `extras`; o oficial terá 30 e 10, respectivamente. As perguntas oficiais usam a distribuição e os campos definidos em `specs/avaliacao/spec.md`.

```yaml
versao: 1
perguntas:
  - id: of-001
    categoria: violencia_e_protecao
    pergunta: "<enunciado fictício escrito pela equipe>"
    autor: "<pessoa autora>"
    resposta_esperada: "<gabarito>"
    pontos_obrigatorios:
      - "<ponto que a resposta deve conter>"
    normas_aceitas:
      - "<norma e dispositivo>"
    fonte: "<referência ao texto legal>"
    conferencia:
      revisor: "<segunda pessoa>"
      fonte_conferida: "<referência consultada>"
extras:
  - id: of-extra-001
    categoria: fora_do_tema
    pergunta: "<enunciado fictício fora do tema>"
    autor: "<pessoa autora>"
```

### Validador do conjunto
O formato normativo está em `specs/avaliacao/spec.md`. O validador confere os campos obrigatórios, a distribuição oficial, o registro de segunda pessoa e chama `app.risco.avaliar` em cada enunciado. Ele não determina se o gabarito está juridicamente correto; essa responsabilidade continua no processo de conferência humana registrado pelo conjunto oficial. O validador também é coberto em `tests/` por fixtures fictícias, sem usar perguntas reais.

### Tecnologias do validador
Os conjuntos usam YAML UTF-8, carregado com PyYAML, que já é dependência do projeto. YAML é legível para a equipe revisar perguntas e gabaritos em alterações de código. O validador usa Python para aplicar regras próprias da avaliação e emitir erros com arquivo e posição. Uma biblioteca de esquema genérica não cobriria por si só a distribuição nem a chamada à regra de risco, e adicionaria pouco para estes dois arquivos.

O validador reutiliza `app.risco.avaliar`, mantendo a verificação de risco alinhada à aplicação sem duplicar padrões. Os testes usam pytest, já disponível no grupo de desenvolvimento, com arquivos temporários e conteúdo fictício; não precisam de serviços externos nem dos conjuntos oficiais.

Para validar a partir da raiz do repositório, execute `uv run python -m scripts.validar_conjuntos desenvolvimento`, `uv run python -m scripts.validar_conjuntos oficial` ou `uv run python -m scripts.validar_conjuntos todos`. O script retorna código diferente de zero e aponta os registros inválidos quando encontra erros.

### Instruções da versão sem RAG
A versão sem RAG remove a regra "Responda usando apenas os trechos". As outras duas frases que mencionam trechos são adaptadas só no necessário para fazer sentido sem eles: mantém-se o formato de citação e a orientação de dizer que não sabe. As duas listas de instruções ficam na rodada, para auditoria. Alternativa descartada: reescrever as instruções da versão sem RAG, que deixaria de ser uma comparação justa.

### Arquivos enviados ao corretor
Cada pergunta tem uma versão sorteada para o arquivo A e a outra para o arquivo B. O sorteio usa uma semente registrada na rodada. Cada arquivo tem 30 respostas e 3 respostas erradas de propósito, escritas pela equipe a partir de perguntas de desenvolvimento, para não alterar as 30 do conjunto oficial. O texto integral dos artigos citados vem do arquivo mais recente de `dados/fontes/dispositivos/`.

### Detecção por código
Recusa é a resposta igual ao texto de recusa do sistema. Presença de citação usa a mesma extração da verificação de citação. Essas duas medidas não vão ao corretor.

### Scripts e arquivos da rodada
- `scripts/rodada.py congelar` valida `oficial.yaml` e grava o hash em `avaliacao/conjuntos/oficial.congelamento.yaml`. `scripts/rodada.py rodar <conjunto> --changelog "<versão>"` grava `registro.yaml` e `respostas.yaml` em `avaliacao/rodadas/<data>-<conjunto>/`, sem sobrescrever rodadas anteriores.
- `scripts/envios.py <rodada>` grava os quatro arquivos em `<rodada>/envios/`, o texto enviado em cada código em `envios/conteudo.yaml` (sem a versão) e o mapa em `<rodada>/mapa.yaml`, fora da pasta dos envios.
- `scripts/conferir.py <rodada>` lê os retornos e grava `<rodada>/resultado.yaml`.

### Respostas erradas de propósito
A equipe escreve as 3 em `avaliacao/conjuntos/erradas.yaml` (`versao: 1` e lista `erradas`), cada uma com `id`, `pergunta_id` de uma pergunta de desenvolvimento, `autor`, `resposta` e `erro` (o que está errado, para conferência). O gabarito e os pontos obrigatórios enviados vêm dessa pergunta de desenvolvimento. As mesmas 3 entram nos dois arquivos, e a última sorteada fica entre as duas últimas linhas. Na rodada de desenvolvimento, a mesma pergunta pode aparecer duas vezes no arquivo, com a resposta real e com a errada.

### Formato do retorno
Cada retorno é salvo como `<rodada>/retornos/<A|B>-<precisao|fidelidade>.json`, uma lista com um objeto por código (aceito também dentro de um bloco ```` ```json ````). O modelo corretor e a data de cada envio ficam em `retornos/registro.yaml`, por exemplo `A-precisao: {modelo: <nome>, data: 2026-11-12}`. A rubrica pede exatamente este formato:

```json
[{"codigo": "A01",
  "pontos": [{"numero": 1, "presente": true, "trecho": "<cópia da resposta>"}],
  "contradiz": false, "trecho_contradicao": ""}]
```

```json
[{"codigo": "A01",
  "afirmacoes": [{"afirmacao": "<cópia da resposta>", "suporte": "sim | nao | fora_da_base",
                  "trecho_artigo": "<cópia do artigo, quando sim>"}]}]
```

### Conferência do retorno
- Linha faltando, código desconhecido ou repetido, JSON inválido ou falta de modelo e data: a correção daquele arquivo não é aceita.
- Resposta errada de propósito aprovada (todos os pontos presentes e sem contradição, ou nenhuma afirmação sem suporte), julgada pelas marcações do corretor: a correção daquele arquivo é rejeitada.
- Trecho que não existe no texto enviado: a linha é apontada e a marcação conta contra a resposta (ponto presente vira ausente, afirmação com suporte vira sem suporte, contradição continua contando). Assim um erro de cópia do corretor nunca melhora a nota. Se as marcações apontadas forem muitas, a equipe decide repetir o envio.
- As métricas usam só os arquivos aceitos e informam quantas respostas foram corrigidas. Afirmações `fora_da_base` ficam fora do percentual sem suporte e são contadas à parte.

## Risks / Trade-offs

- **Sem revisão humana, um erro sistemático do corretor passa despercebido** → Respostas erradas de propósito, trechos comprobatórios e a declaração no relatório.
- **O método diverge do documento da Semana 1 em `docs/` (50 perguntas e revisão em dupla)** → O grupo aceitou a mudança em 12/11 (#9), e a aceitação do grupo basta, sem confirmar com o curso. O relatório declara que o método mudou.
- **O corretor pode truncar 33 linhas em uma conversa** → O teste com as perguntas de desenvolvimento valida o formato, e o script aponta linhas faltantes.
- **O nome `deepseek-flash` não fixa uma versão** → Rodar as duas versões no mesmo dia e registrar nome, data e versão do changelog.
- **As perguntas podem ficar prontas só no meio da quinta** → A rodada pode passar para a manhã de sexta, e o relatório continua sendo a prioridade.

## Open Questions

- Qual LLM externo será usado. A escolha precisa sair antes do teste de quinta e é registrada na tarefa correspondente. Se ele não aceitar o formato, muda-se o modelo, sem mudar as specs.
