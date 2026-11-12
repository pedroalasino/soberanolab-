import hashlib
import json
import time
from collections import defaultdict
from datetime import datetime

import config

ARCHIVO = config.CARPETA / "logs" / "soberai.jsonl"

def registrar(agente, sesion, mensaje, resultado, inicio, error=None):
    """Anota cada pedido. Por privacidad NO guarda el texto: solo su largo y un código de sesión."""
    ARCHIVO.parent.mkdir(exist_ok=True)
    evento = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "agente": agente,
        "sesion": hashlib.sha256(sesion.encode()).hexdigest()[:10],
        "largo_mensaje": len(mensaje),
        "latencia_ms": round((time.time() - inicio) * 1000),
        "tokens": (resultado or {}).get("tokens", 0),
        "herramientas": (resultado or {}).get("herramientas", []),
        "error": error,
    }
    with open(ARCHIVO, "a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")

def resumen():
    if not ARCHIVO.exists():
        print("Todavía no hay registros.")
        return
    por_agente = defaultdict(list)
    for linea in ARCHIVO.read_text(encoding="utf-8").splitlines():
        e = json.loads(linea)
        por_agente[e["agente"]].append(e)
    for agente, eventos in por_agente.items():
        n = len(eventos)
        latencia = sum(e["latencia_ms"] for e in eventos) / n
        tokens = sum(e["tokens"] for e in eventos)
        errores = sum(1 for e in eventos if e["error"])
        print(f"{agente}: {n} pedidos | latencia promedio {latencia:.0f} ms | {tokens} tokens | {errores} errores")

if __name__ == "__main__":
    resumen()
