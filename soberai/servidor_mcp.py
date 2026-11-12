"""
Servidor MCP de SOBERAI: el motor expone sus agentes con el enchufe estándar.
Solo lectura: se puede consultar, nunca modificar. En modo stdio no se usa print() (ensucia el canal).
"""
import uuid

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

import config
import conocimiento
import motor

SOLO_LECTURA = ToolAnnotations(readOnlyHint=True, destructiveHint=False)
servidor = MCPServer(name="soberai", instructions="Motor de IA de SoberanoLab. Herramientas de solo lectura.")

def validar(agente, texto):
    if agente not in motor.FICHAS:
        raise ToolError(f"No existe el agente {agente}. Usá listar_agentes.")
    texto = (texto or "").strip()
    if not texto or len(texto) > config.MAX_LARGO:
        raise ToolError(f"El texto tiene que tener entre 1 y {config.MAX_LARGO} caracteres.")
    return texto

@servidor.tool(annotations=SOLO_LECTURA)
def listar_agentes() -> str:
    """Lista los agentes que corren en el motor SOBERAI."""
    return "\n".join(f"{n}: {f.descripcion}" for n, f in motor.FICHAS.items())

@servidor.tool(annotations=SOLO_LECTURA)
def buscar(agente: str, consulta: str) -> str:
    """Busca en los documentos de un agente, sin usar el modelo. Rápido."""
    consulta = validar(agente, consulta)
    resultados = conocimiento.base(agente).buscar(consulta)
    if not resultados:
        return "No encontré nada sobre eso en los documentos de ese agente."
    return "\n\n".join(f"[{r['fuente']}] {r['texto']}" for r in resultados)

@servidor.tool(annotations=SOLO_LECTURA)
def preguntar(agente: str, mensaje: str) -> str:
    """Le hace una pregunta a un agente del motor. Pasa por la guardia y responde con el modelo local."""
    mensaje = validar(agente, mensaje)
    return motor.conversar(agente, f"mcp-{uuid.uuid4().hex[:8]}", mensaje)["respuesta"]

if __name__ == "__main__":
    servidor.run("stdio")
