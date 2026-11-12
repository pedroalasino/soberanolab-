from langchain_core.tools import StructuredTool

import agentes
import config
import conocimiento

def crear_buscar(agente):
    def buscar_conocimiento(consulta: str) -> str:
        consulta = (consulta or "").strip()[:200]
        resultados = conocimiento.base(agente).buscar(consulta)
        if not resultados:
            return "No encontré nada sobre eso en los documentos."
        return "\n\n".join(f"[{r['fuente']}] {r['texto']}" for r in resultados)
    return StructuredTool.from_function(
        buscar_conocimiento, name="buscar_conocimiento",
        description="Busca información en los documentos de este agente.")

def crear_estado(agente):
    def estado_motor() -> str:
        modelos = ", ".join(f"{rol}: {m}" for rol, m in config.MODELOS.items())
        nombres = ", ".join(agentes.cargar_agentes())
        return f"Modelos: {modelos}. Agentes: {nombres}. Todo corre con Ollama, sin servicios de terceros."
    return StructuredTool.from_function(
        estado_motor, name="estado_motor",
        description="Muestra qué modelos y agentes tiene cargados el motor SOBERAI.")

FABRICAS = {"buscar_conocimiento": crear_buscar, "estado_motor": crear_estado}

def herramientas_para(ficha):
    permitidas = {}
    for nombre in ficha.herramientas:
        if nombre not in FABRICAS:
            raise ValueError(f"El agente {ficha.nombre} pide una herramienta que no existe: {nombre}")
        herramienta = FABRICAS[nombre](ficha.nombre)
        permitidas[herramienta.name] = herramienta
    return permitidas
