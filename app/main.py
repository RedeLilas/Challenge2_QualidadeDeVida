"""Aplicação FastAPI: rotas do backend (e, a partir da tarefa 2.1, a PWA em web/)."""
import logging

from fastapi import FastAPI

from app.logs import registrar_requisicao

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="Rede Lilás")
app.middleware("http")(registrar_requisicao)


@app.get("/saude")
def saude() -> dict:
    return {"status": "ok"}
