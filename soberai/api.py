import json
import os
import secrets
import time
from collections import defaultdict, deque

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from langchain_core.messages import AIMessageChunk, HumanMessage
from pydantic import BaseModel, Field

import config
import motor
import observabilidad

# Clientes y sus claves: vienen de una variable de entorno, NUNCA del código.
# Ejemplo: SOBERAI_CLIENTES={"clave-larga-1": ["portfolio"], "clave-larga-2": ["portfolio", "soberanolab"]}
CLIENTES = json.loads(os.getenv("SOBERAI_CLIENTES", "{}"))
if not CLIENTES:
    print("[api] Sin SOBERAI_CLIENTES: uso la clave de práctica 'demo-local' con todos los agentes.")
    CLIENTES = {"demo-local": list(motor.FICHAS)}

pedidos = defaultdict(deque)
app = FastAPI(title="SOBERAI", description="Motor de IA de SoberanoLab")

class Pedido(BaseModel):
    sesion: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    mensaje: str = Field(min_length=1, max_length=config.MAX_LARGO)

def cliente_autorizado(x_api_key: str = Header(default="")):
    for clave, agentes in CLIENTES.items():
        if secrets.compare_digest(x_api_key, clave):  # compara sin filtrar pistas por tiempo
            ahora, cola = time.time(), pedidos[clave]
            while cola and ahora - cola[0] > 60:
                cola.popleft()
            if len(cola) >= config.LIMITE_POR_MINUTO:
                raise HTTPException(429, "Demasiados pedidos. Esperá un minuto.")
            cola.append(ahora)
            return agentes
    raise HTTPException(401, "API key inválida.")

def validar_agente(agente, permitidos):
    if agente not in motor.FICHAS:
        raise HTTPException(404, f"No existe el agente {agente}.")
    if agente not in permitidos:
        raise HTTPException(403, f"Tu clave no tiene permiso para el agente {agente}.")

@app.get("/salud")
def salud():
    return {"estado": "ok", "agentes": list(motor.FICHAS), "modelos": config.MODELOS}

@app.get("/v1/agentes")
def listar(permitidos=Depends(cliente_autorizado)):
    return [{"nombre": n, "descripcion": motor.FICHAS[n].descripcion} for n in permitidos]

@app.post("/v1/chat/{agente}")
def chat(agente: str, pedido: Pedido, permitidos=Depends(cliente_autorizado)):
    validar_agente(agente, permitidos)
    inicio = time.time()
    try:
        resultado = motor.conversar(agente, pedido.sesion, pedido.mensaje)
    except Exception as error:
        observabilidad.registrar(agente, pedido.sesion, pedido.mensaje, None, inicio, error.__class__.__name__)
        raise HTTPException(503, "El motor no pudo responder. Probá de nuevo en un rato.")
    observabilidad.registrar(agente, pedido.sesion, pedido.mensaje, resultado, inicio)
    return resultado

def eventos(agente, pedido):
    """Genera la respuesta en pedacitos (streaming), para la API y para la página pública."""
    hilo = {"configurable": {"thread_id": f"{agente}:{pedido.sesion}"}}
    entrada = {"messages": [HumanMessage(pedido.mensaje)], "agente": agente}
    hubo_texto = False
    for pedazo, meta in motor.app.stream(entrada, hilo, stream_mode="messages"):
        if (meta.get("langgraph_node") == "agente" and isinstance(pedazo, AIMessageChunk)
                and pedazo.content and not pedazo.tool_call_chunks):
            hubo_texto = True
            yield f"data: {json.dumps({'texto': pedazo.content}, ensure_ascii=False)}\n\n"
    if not hubo_texto:  # respuesta fija de la guardia
        final = motor.app.get_state(hilo).values["messages"][-1].content
        yield f"data: {json.dumps({'texto': final}, ensure_ascii=False)}\n\n"
    yield "data: [FIN]\n\n"

@app.post("/v1/chat/{agente}/stream")
def chat_stream(agente: str, pedido: Pedido, permitidos=Depends(cliente_autorizado)):
    validar_agente(agente, permitidos)
    return StreamingResponse(eventos(agente, pedido), media_type="text/event-stream")

# ---------- Página pública: la puede usar cualquiera, sin clave, con límite por persona ----------
WEB = config.CARPETA / "web"
PUBLICOS = os.getenv("SOBERAI_PUBLICOS", ",".join(motor.FICHAS)).split(",")

@app.get("/")
def pagina():
    return FileResponse(WEB / "index.html")

@app.get("/web/logo.png")
def logo():
    return FileResponse(WEB / "logo.png")

@app.post("/publico/chat/{agente}/stream")
def chat_publico(agente: str, pedido: Pedido, request: Request):
    ip = request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "?")
    ahora, cola = time.time(), pedidos[f"ip:{ip}"]
    while cola and ahora - cola[0] > 60:
        cola.popleft()
    if len(cola) >= config.LIMITE_POR_MINUTO:
        raise HTTPException(429, "Demasiados pedidos. Esperá un minuto.")
    cola.append(ahora)
    validar_agente(agente, PUBLICOS)
    return StreamingResponse(eventos(agente, pedido), media_type="text/event-stream")
