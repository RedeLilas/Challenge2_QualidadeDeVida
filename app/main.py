"""Aplicação FastAPI: rotas do backend (e, a partir da tarefa 2.1, a PWA em web/)."""
from fastapi import FastAPI

app = FastAPI(title="Rede Lilás")


@app.get("/saude")
def saude() -> dict:
    return {"status": "ok"}
