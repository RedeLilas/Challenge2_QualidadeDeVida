# Proposal

## Why

Um dos objetivos do projeto é mostrar quais benefícios provavelmente se aplicam ao caso da usuária e o que falta para acessá-los. As regras precisam ser determinísticas e auditáveis, e o formato do resultado serve de contrato comum para os agentes da S4, que tem só dois dias.

Métrica do ROADMAP afetada: acurácia de elegibilidade (≥ 90%), medida na S4.

## What Changes

- Regras de Bolsa Família, BPC, auxílio-aluguel (Lei 11.340/2006) e Aluguel Social do DF, em arquivo versionado, com norma, artigo, vigência e data de verificação.
- Quarto resultado: "faltam informações".
- Renda per capita calculada no aparelho, considerando a casa como ficará sem o agressor.
- Salário mínimo como valor versionado, com fonte e data.
- Execução só no navegador, usando o perfil e, em memória, as perguntas específicas de cada benefício.
- Orientação para procurar o CRAS mais próximo. A lista de CRAS fica para a S4.
- Formato comum de resultado para os agentes da S4.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `beneficios`: acrescenta "faltam informações", adia a lista de CRAS, define as quatro regras e o cálculo no aparelho e ajusta o uso sem perfil.

## Impact

- **Novos arquivos:** `regras/beneficios.json`, `web/beneficios.js`, testes em `tests/`.
- **Código alterado:** `web/index.html`, `web/app.js`, `web/sw.js`.
- **Depende de:** `s3-frontend-e-perfil` (navegação e formulário).
- **Privacidade (LGPD):** nenhum nome ou documento é pedido. O cálculo roda no aparelho, e nada é enviado ao servidor ou ao LLM. As perguntas específicas ficam só em memória.
- **Segurança da usuária:** nenhum resultado afirma direito garantido. A regra do boletim no Aluguel Social é interpretação da equipe, sem validação jurídica, e o resultado avisa que o órgão ainda pode pedir a medida protetiva.
- **Fora desta mudança:** lista de CRAS e agente de benefícios (S4), outros benefícios distritais de `dados/normas.csv`, validação jurídica externa.
