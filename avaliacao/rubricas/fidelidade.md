# Rubrica de fidelidade

Você vai verificar se as afirmações de respostas sobre leis brasileiras têm apoio no texto das leis que elas citam. Depois destas instruções vêm vários blocos. Cada bloco começa com uma linha `=== <código> ===` e traz:

- RESPOSTA: o texto a verificar;
- ARTIGOS CITADOS (texto integral): o texto oficial dos artigos citados na resposta, cada um com seu rótulo entre colchetes, ou "(nenhum)";
- CITAÇÕES FORA DA BASE: artigos citados na resposta cujo texto não foi fornecido, ou "(nenhuma)".

Use apenas o texto dos ARTIGOS CITADOS do mesmo bloco. Não use conhecimento próprio sobre a lei, não pesquise e não compare com outros blocos.

## Passo 1: separar as afirmações

Liste cada afirmação da RESPOSTA sobre o que a lei diz: direitos, deveres, proibições, prazos, penas, quem pode fazer o quê, condições e definições.

- Cada afirmação é a cópia de um pedaço contínuo da RESPOSTA: a frase inteira, ou parte dela quando a frase traz mais de uma afirmação.
- Não liste cumprimentos, frases de acolhimento, conselhos práticos que a RESPOSTA não atribui à lei (como procurar ajuda ou guardar provas) nem frases que só dizem que não sabe responder.
- Toda RESPOSTA que diz algo sobre a lei tem pelo menos uma afirmação. Só devolva `"afirmacoes": []` quando a RESPOSTA não diz nada sobre a lei.

## Passo 2: classificar o suporte

- `"sim"`: o texto de um dos ARTIGOS CITADOS diz o mesmo que a afirmação, mesmo com outras palavras. Números, prazos, penas, sujeitos e condições precisam coincidir. Copie em `trecho_artigo` o pedaço do artigo que comprova a afirmação.
- `"nao"`: o texto dos ARTIGOS CITADOS contradiz a afirmação ou não traz nada que a comprove. Inclui a afirmação que acrescenta condição, exceção ou detalhe que o artigo não tem.
- `"fora_da_base"`: a afirmação depende de um artigo listado em CITAÇÕES FORA DA BASE, e os ARTIGOS CITADOS não a confirmam nem a contradizem.
- Se os ARTIGOS CITADOS contradizem a afirmação, o suporte é `"nao"`, mesmo que ela também cite um artigo fora da base.
- Na dúvida entre `"sim"` e `"nao"`, use `"nao"`: o apoio precisa estar escrito no artigo.
- Com `"nao"` ou `"fora_da_base"`, `trecho_artigo` é `""`.

## Trechos copiados

- `afirmacao` e `trecho_artigo` são cópias exatas: as mesmas palavras, acentos, maiúsculas e pontuação.
- Copie um único pedaço contínuo. Não junte pedaços, não use reticências e não resuma.
- `trecho_artigo` sai do texto dos ARTIGOS CITADOS, sem o rótulo entre colchetes.
- Um trecho que não existe no texto enviado invalida a marcação.

## Formato da saída

Devolva só um JSON: uma lista com um objeto para cada bloco, na ordem dos blocos, sem pular nenhum. Não escreva nada antes nem depois do JSON.

```json
[
  {
    "codigo": "A01",
    "afirmacoes": [
      {"afirmacao": "<cópia da RESPOSTA>", "suporte": "sim", "trecho_artigo": "<cópia do artigo>"},
      {"afirmacao": "<cópia da RESPOSTA>", "suporte": "nao", "trecho_artigo": ""}
    ]
  }
]
```

- `codigo`: igual ao da linha `=== <código> ===`.
- `suporte`: exatamente `"sim"`, `"nao"` (sem acento) ou `"fora_da_base"`.
- Antes de terminar, confira se há um objeto para cada código, do primeiro ao último bloco.
