#!/usr/bin/env python3
"""Servidor local leve da Rede Lilás para testar o front-end no navegador sem dependências externas.

Serve:
- / e todos os arquivos de web/ (index.html, styles.css, perfil.js, dados.js, app.js, sw.js)
- /regras/risco_imediato.json
- GET /rede-protecao (lê os 20 serviços oficiais de dados/rede_protecao_df.csv)
- POST /juridico (checa risco imediato 190 e devolve resposta fundamentada com citações)
"""
import csv
import http.server
import json
import socketserver
import sys
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from app import risco

WEB = RAIZ / "web"
REGRAS = RAIZ / "regras"
DADOS = RAIZ / "dados"
PORTA = 8080


class HandlerRedeLilas(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def end_headers(self):
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self):
        caminho = urlparse(self.path).path
        if caminho == "/saude":
            return self._json({"status": "ok"})
        if caminho == "/rede-protecao":
            with (DADOS / "rede_protecao_df.csv").open(encoding="utf-8") as f:
                return self._json(list(csv.DictReader(f)))
        if caminho.startswith("/regras/") and caminho.endswith(".json"):
            nome_arquivo = Path(caminho).name
            alvo = REGRAS / nome_arquivo
            if alvo.is_file():
                dados = json.loads(alvo.read_text(encoding="utf-8"))
                return self._json(dados)
        return super().do_GET()

    def do_POST(self):
        caminho = urlparse(self.path).path
        tamanho = int(self.headers.get("Content-Length", "0"))
        corpo = json.loads(self.rfile.read(tamanho).decode("utf-8") or "{}")
        texto = corpo.get("pergunta") or corpo.get("texto") or ""

        if resultado := risco.avaliar(texto):
            return self._json(
                {"risco_imediato": True, "categoria": resultado["categoria"], "resposta": risco.ALERTA}
            )

        if caminho in ("/juridico", "/mensagem"):
            return self._json(_resposta_demonstracao(texto))

        self.send_error(404)

    def _json(self, dados, status=200):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(corpo)


def _resposta_demonstracao(pergunta: str) -> dict:
    p = pergunta.lower()
    if "medida" in p or "protetiva" in p or "boletim" in p or "afastar" in p:
        return {
            "resposta": (
                "Pela Lei Maria da Penha (Lei 11.340/2006, art. 19, §§ 4º a 6º, incluídos pela Lei 14.550/2023), "
                "as medidas protetivas de urgência podem ser concedidas pelo juiz a partir do seu depoimento na "
                "delegacia (DEAM) ou de alegações apresentadas pela Defensoria Pública, sem exigir boletim de "
                "ocorrência prévio nem inquérito policial concluído."
            ),
            "citacoes": [
                {"citacao": "Lei 11.340/2006, arts. 19 e 22", "data_acesso": "2026-11-05"},
                {"citacao": "Lei 14.550/2023, art. 1º", "data_acesso": "2026-11-05"},
            ],
            "recusada": False,
        }
    if "aluguel" in p or "benefício" in p or "beneficio" in p or "bolsa" in p or "dinheiro" in p:
        return {
            "resposta": (
                "No Distrito Federal, mulheres em situação de violência doméstica podem solicitar o Aluguel Social "
                "do DF no valor de R$ 600,00 mensais por até 6 meses, prorrogável (Lei Distrital 6.623/2020 e "
                "Portaria SMDF 49/2026), além do Auxílio-Aluguel judicial previsto na Lei Maria da Penha "
                "(Lei 11.340/2006, art. 23, VI, incluído pela Lei 14.674/2023). Não ter CadÚnico ativo não impede "
                "o pedido inicial do Aluguel Social do DF."
            ),
            "citacoes": [
                {"citacao": "Portaria SMDF 49/2026, arts. 4º, 5º e 15", "data_acesso": "2026-11-05"},
                {"citacao": "Lei 11.340/2006, art. 23, VI (Lei 14.674/2023)", "data_acesso": "2026-11-05"},
            ],
            "recusada": False,
        }
    if "24h" in p or "atendimento" in p or "delegacia" in p or "deam" in p or "onde" in p:
        return {
            "resposta": (
                "No Distrito Federal, funcionam 24 horas todos os dias: a Casa da Mulher Brasileira de Ceilândia "
                "(CNM 1, Bloco I, Lote 3 — tel. 3181-1474), a DEAM I na Asa Sul (EQS 204/205 — tel. 3207-6172) e a "
                "DEAM II em Ceilândia (QNM 02 — tel. 3207-7391). Para orientação jurídica e psicossocial gratuita, "
                "você também pode procurar os CEAMs ou o NUDEM da Defensoria Pública (Disque 129)."
            ),
            "citacoes": [
                {"citacao": "Rede de Proteção do DF · dados oficiais", "data_acesso": "2026-11-05"},
            ],
            "recusada": False,
        }
    return {
        "resposta": (
            "A Lei Maria da Penha (Lei 11.340/2006, arts. 5º e 7º) protege mulheres contra violência física, "
            "psicológica, sexual, patrimonial e moral, garantindo medidas protetivas de urgência, manutenção do "
            "vínculo trabalhista por até 6 meses (art. 9º, § 2º, II) e atendimento prioritário. Para orientação "
            "gratuita 24h, ligue 180."
        ),
        "citacoes": [
            {"citacao": "Lei 11.340/2006, arts. 5º, 7º e 9º", "data_acesso": "2026-11-05"},
        ],
        "recusada": False,
    }


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(RAIZ))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORTA), HandlerRedeLilas) as httpd:
        print(f"Servidor local Rede Lilás rodando em: http://127.0.0.1:{PORTA}")
        httpd.serve_forever()
