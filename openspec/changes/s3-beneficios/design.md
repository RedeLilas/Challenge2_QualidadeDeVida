# Design

## Context

As normas dos quatro benefícios já estão na base, coletadas em 03/11. O salário mínimo não tem fonte no repositório, e reajustes por decreto, como o dos R$ 218, não foram verificados. `dados/rede_protecao_df.csv` não tem CRAS. O formulário de perfil vem de `s3-frontend-e-perfil`.

## Goals / Non-Goals

**Goals:**
- Regras auditáveis, com a referência legal exibida junto ao resultado.
- Um formato de resultado que os agentes da S4 possam reutilizar.

**Non-Goals:**
- Confirmar direito ou calcular valor do benefício.
- Cobrir outros benefícios distritais.

## Decisions

### Mesmo modelo da triagem
`regras/beneficios.json` guarda versão, salário mínimo com fonte e data, requisitos, textos e, em cada regra, norma, artigo, início de vigência e data de verificação. `web/beneficios.js` é uma função pura, testada em QuickJS. Alternativa descartada: regras no servidor, que exigiria enviar dados da usuária.

### Contrato comum de resultado
Cada benefício produz:

```json
{
  "id": "bolsa_familia",
  "status": "provavel | depende_decisao_judicial | nao_aplicavel | faltam_informacoes",
  "rotulo": "texto exibido",
  "motivos": [],
  "falta": [],
  "onde_pedir": "",
  "fontes": [{ "norma": "", "artigo": "", "inicio_vigencia": "", "data_verificacao": "" }],
  "aviso": ""
}
```

Os agentes da S4 recebem as respostas e devolvem esse formato, com `fontes` como citações. "Não aplicável por enquanto" é o `rotulo` de um `status` igual a `nao_aplicavel`, para manter quatro estados. Alternativa descartada: criar um quinto estado, que os agentes da S4 teriam de tratar à parte.

### Dados do perfil e perguntas específicas
Vêm do perfil: localização, renda total, número de pessoas, CadÚnico, idade e medida protetiva. São perguntados em Benefícios, só em memória: deficiência, boletim de ocorrência, acompanhamento psicossocial e necessidade de moradia. A pergunta de renda deixa claro que deve considerar a casa como ficará sem o agressor.

### Requisito de moradia do Aluguel Social
A decisão de 09/11 listou moradia, renda e acompanhamento. A Portaria 49/2026, art. 5º, IV, também exige necessidade de saída emergencial do lar ou de permanecer no imóvel alugado. A spec exige regras escritas a partir do texto legal, então o requisito entra na regra.

### Limites inclusivos
"Até" inclui o valor do limite em todas as regras, como no texto legal ("igual ou inferior").

## Risks / Trade-offs

- **O valor de R$ 218 e o salário mínimo podem ter sido reajustados** → A verificação é a primeira tarefa, e cada resultado exibe a data da regra.
- **A regra do boletim é interpretação da equipe, sem validação jurídica** → O resultado avisa que o órgão ainda pode pedir a medida, e a limitação vai para o relatório.
- **Falsa expectativa** → Todo resultado diz que a concessão depende do órgão responsável, e nenhum texto usa "direito garantido".
- **Regras novas erradas passam despercebidas até a S4** → Testes com casos fictícios cobrem cada limite, cada requisito e cada resultado.
