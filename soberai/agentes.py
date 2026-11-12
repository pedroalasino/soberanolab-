import json

from pydantic import BaseModel, Field

import config

class FichaAgente(BaseModel):
    nombre: str = Field(pattern=r"^[a-z0-9_-]+$")
    descripcion: str
    modelo: str = "chat"
    herramientas: list[str] = []
    prompt: str = Field(min_length=20)

def cargar_agentes():
    agentes = {}
    for archivo in sorted((config.CARPETA / "agentes").glob("*.json")):
        ficha = FichaAgente(**json.loads(archivo.read_text(encoding="utf-8")))
        config.modelo(ficha.modelo)  # valida que el rol de modelo exista
        agentes[ficha.nombre] = ficha
    return agentes
