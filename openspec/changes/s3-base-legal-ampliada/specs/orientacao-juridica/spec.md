# Spec Delta

## ADDED Requirements

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
