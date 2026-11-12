import os
from pathlib import Path

CARPETA = Path(__file__).parent
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

MODELOS = {
    "chat":       os.getenv("SOBERAI_CHAT", "qwen2.5:3b"),
    "respaldo":   os.getenv("SOBERAI_RESPALDO", "qwen2.5:3b"),
    "embeddings": os.getenv("SOBERAI_EMBEDDINGS", "nomic-embed-text"),
}

MAX_PASOS = 5
MAX_LARGO = 500
MAX_HISTORIAL = 12
LIMITE_POR_MINUTO = 20

def modelo(rol):
    if rol not in MODELOS:
        raise ValueError(f"Rol de modelo desconocido: {rol}")
    return MODELOS[rol]
