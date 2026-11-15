# Rubrica de precisão

Você vai corrigir respostas a perguntas sobre os direitos de mulheres em situação de violência doméstica no Brasil. Depois destas instruções vêm vários blocos. Cada bloco começa com uma linha `=== <código> ===` e traz:

- PERGUNTA: o que foi perguntado;
- GABARITO: a resposta correta, conferida no texto da lei;
- PONTOS OBRIGATÓRIOS: a lista numerada do que uma resposta correta precisa conter;
- RESPOSTA: o texto a corrigir.

Julgue cada RESPOSTA só contra o GABARITO e os PONTOS OBRIGATÓRIOS do mesmo bloco. Não use conhecimento próprio sobre a lei, não pesquise e não compare com outros blocos.

## Pontos obrigatórios

- `"presente": true` quando a RESPOSTA afirma o mesmo conteúdo do ponto, mesmo com outras palavras. Números, prazos, penas, quem pode fazer o quê e condições precisam coincidir com o ponto.
- `"presente": false` quando a RESPOSTA não trata do ponto, trata dele de forma vaga demais para conferir ou diz algo diferente dele.
- Com `"presente": true`, `trecho` é a cópia do pedaço da RESPOSTA que mostra o ponto. Com `"presente": false`, `trecho` é `""`.

## Contradição

- `"contradiz": true` quando alguma frase da RESPOSTA é incompatível com o GABARITO ou com um ponto obrigatório: número, prazo ou pena diferente, regra invertida, ou exigência, restrição ou exceção que não pode valer junto com o gabarito. Copie essa frase em `trecho_contradicao`.
- Informação a mais que não conflita com o GABARITO não é contradição.
- Com `"contradiz": false`, `trecho_contradicao` é `""`.
- Se a RESPOSTA só disser que não sabe responder, marque todos os pontos como ausentes e `"contradiz": false`.

## Trechos copiados

- Copie exatamente como está na RESPOSTA: as mesmas palavras, acentos, maiúsculas e pontuação.
- Copie um único pedaço contínuo, de preferência uma frase ou parte dela. Não junte pedaços, não use reticências, não resuma e não corrija erros.
- Um trecho que não existe na RESPOSTA invalida a marcação.

## Formato da saída

Devolva só um JSON: uma lista com um objeto para cada bloco, na ordem dos blocos, sem pular nenhum. Não escreva nada antes nem depois do JSON.

```json
[
  {
    "codigo": "A01",
    "pontos": [
      {"numero": 1, "presente": true, "trecho": "<cópia da RESPOSTA>"},
      {"numero": 2, "presente": false, "trecho": ""}
    ],
    "contradiz": false,
    "trecho_contradicao": ""
  }
]
```

- `codigo`: igual ao da linha `=== <código> ===`.
- `pontos`: um item para cada ponto obrigatório do bloco, com `numero` igual ao da lista (1, 2, 3...).
- `presente` e `contradiz`: `true` ou `false`, sem aspas.
- Antes de terminar, confira se há um objeto para cada código, do primeiro ao último bloco.
