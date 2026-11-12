"""Prende el motor, prueba la API y lo apaga. Si el motor no arranca, muestra por qué."""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

CARPETA = Path(__file__).parent
URL = "http://localhost:8001"
CLAVE = {"x-api-key": "demo-local", "Content-Type": "application/json"}

def pedir(ruta, datos=None):
    cuerpo = json.dumps(datos).encode("utf-8") if datos else None
    pedido = urllib.request.Request(URL + ruta, data=cuerpo, headers=CLAVE)
    return urllib.request.urlopen(pedido, timeout=120)

registro = open(CARPETA / "motor.log", "w", encoding="utf-8")
motor = subprocess.Popen([sys.executable, "-m", "uvicorn", "api:app", "--port", "8001"],
                         cwd=CARPETA, stdout=registro, stderr=subprocess.STDOUT)
print("Prendiendo el motor", end="", flush=True)
try:
    for _ in range(60):
        if motor.poll() is not None:
            registro.close()
            print("\nEl motor no arrancó. Esto dijo:\n")
            print((CARPETA / "motor.log").read_text(encoding="utf-8"))
            sys.exit(1)
        try:
            pedir("/salud")
            break
        except Exception:
            print(".", end="", flush=True)
            time.sleep(1)
    print(" listo\n")

    print("SALUD:", pedir("/salud").read().decode(), "\n")
    print("CHAT:", pedir("/v1/chat/soberanolab", {"sesion": "p1", "mensaje": "¿Qué es SOBERAI?"}).read().decode(), "\n")
    print("STREAM: ", end="")
    for linea in pedir("/v1/chat/portfolio/stream", {"sesion": "p2", "mensaje": "¿Dónde vive Pedro?"}):
        linea = linea.decode().strip()
        if linea.startswith("data: ") and linea != "data: [FIN]":
            print(json.loads(linea[6:])["texto"], end="", flush=True)
    print()
finally:
    motor.terminate()
    print("\nMotor apagado.")
