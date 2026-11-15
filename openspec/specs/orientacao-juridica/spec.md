# orientacao-juridica Specification

## Purpose
Ajudar a usuária a reconhecer se o que vive é violência prevista em lei e quais direitos tem, com respostas fundamentadas no texto oficial da Lei Maria da Penha (via RAG) e sempre com o artigo citado. Origem: RF02, RNF03, RNF06.

## Requirements

### Requirement: Resposta fundamentada com citação
Toda resposta jurídica SHALL citar a norma, o artigo (e inciso, quando houver) e a data em que o texto foi verificado. O sistema MUST usar apenas trechos recuperados da base legal para fundamentar a resposta.

#### Scenario: Pergunta sobre medida protetiva
- **WHEN** a usuária pergunta "o que é medida protetiva e como peço?"
- **THEN** a resposta explica em linguagem simples e cita os artigos da Lei 11.340/2006 que a fundamentam, com a data de verificação

#### Scenario: Citação conferida
- **WHEN** o LLM gera uma resposta citando um artigo que não está entre os trechos recuperados
- **THEN** o sistema descarta a resposta e não a exibe

### Requirement: Identificação das formas de violência
O sistema SHALL identificar, a partir do relato, quais formas de violência do art. 7º da Lei Maria da Penha podem estar presentes (física, psicológica, sexual, patrimonial, moral), explicando cada uma em linguagem simples.

#### Scenario: Relato da persona Camila
- **WHEN** a usuária escreve "ele nunca me bateu, só quebrou minhas coisas e me humilhou, isso conta?"
- **THEN** o sistema indica possível violência patrimonial (art. 7º, IV) e psicológica (art. 7º, II), com a citação

### Requirement: Recusa sem fundamentação
Quando não houver trecho recuperado que sustente a resposta, o sistema SHALL dizer que não sabe responder com segurança e MUST indicar o Ligue 180 e a Defensoria Pública do DF, sem inventar conteúdo.

#### Scenario: Pergunta fora da base legal
- **WHEN** a usuária pergunta sobre partilha de bens em detalhe processual que a base não cobre
- **THEN** o sistema recusa a resposta e indica o Ligue 180 e a Defensoria Pública do DF

### Requirement: Base legal versionada
Cada trecho da base legal SHALL guardar a URL oficial de origem e a data de acesso. A base MUST ser revisada ao menos uma vez por mês durante o projeto.

#### Scenario: Data exibida
- **WHEN** uma resposta jurídica é exibida
- **THEN** ela mostra a data da última verificação do texto legal usado

### Requirement: Limite da orientação jurídica
O sistema SHALL deixar claro que oferece orientação e não substitui advogada ou defensora, e MUST NOT redigir petições judiciais.

#### Scenario: Pedido de petição
- **WHEN** a usuária pede "escreve o pedido de medida protetiva para eu entregar ao juiz"
- **THEN** o sistema explica que não redige petições e indica onde obter atendimento gratuito no DF

### Requirement: Cobertura penal e de guarda da base legal
A base legal SHALL conter o texto oficial dos arts. 121-A, 129, 138, 139, 140, 147, 147-A, 147-B, 148, 163, 181, 182, 183, 213, 215-A e 218-C do Código Penal, do art. 1.584 do Código Civil e do art. 699-A do Código de Processo Civil, cada trecho com URL oficial e data de acesso.

#### Scenario: Pergunta sobre crime
- **WHEN** a usuária pergunta se xingamentos na frente de outras pessoas podem ser crime
- **THEN** os trechos recuperados podem incluir os arts. 138 a 140 do Código Penal, e a resposta cita o artigo usado com a data de verificação

#### Scenario: Pergunta sobre guarda
- **WHEN** a usuária pergunta se a violência doméstica interfere na guarda dos filhos
- **THEN** os trechos recuperados podem incluir o art. 1.584 do Código Civil e o art. 699-A do Código de Processo Civil, e a resposta cita o artigo usado com a data de verificação

#### Scenario: Conferência da cobertura
- **WHEN** a base é gerada a partir das fontes oficiais
- **THEN** cada artigo listado neste requisito tem ao menos um trecho e um dispositivo com o texto integral

### Requirement: Citação de artigo com separador de milhar
O sistema SHALL ler e conferir artigos escritos com separador de milhar pelo número completo, tanto na coleta quanto na verificação de citação.

#### Scenario: Coleta do art. 1.584
- **WHEN** o texto oficial traz "Art. 1.584."
- **THEN** o dispositivo é registrado como art. 1.584, e não como art. 1

#### Scenario: Citação conferida com separador
- **WHEN** a resposta cita "Código Civil, art. 1.584" e esse artigo está entre os trechos recuperados
- **THEN** a citação é aceita e exibida como art. 1.584

#### Scenario: Citação de artigo não recuperado
- **WHEN** a resposta cita "Código Civil, art. 1.584" e os trechos recuperados só trazem o art. 1 de outra norma
- **THEN** o sistema descarta a resposta e não a exibe

#### Scenario: Artigos sem separador continuam iguais
- **WHEN** a resposta cita "Lei 11.340/2006, art. 7º" ou o texto oficial traz "Art. 147 - Ameaçar"
- **THEN** a leitura continua sendo art. 7 e art. 147
