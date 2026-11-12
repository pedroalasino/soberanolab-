"""Cliente MCP de prueba: prende el servidor de SOBERAI, lista sus herramientas y las usa."""
import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

SERVIDOR = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).parent / "servidor_mcp.py")])

PRUEBAS = [
    ("listar_agentes", {}),
    ("buscar", {"agente": "soberanolab", "consulta": "privacidad"}),
    ("preguntar", {"agente": "portfolio", "mensaje": "¿Dónde vive Pedro?"}),
    ("buscar", {"agente": "no-existe", "consulta": "hola"}),       # trampa
    ("borrar_agente", {"agente": "portfolio"}),                     # trampa
]

async def main():
    async with Client(SERVIDOR) as cliente:
        print("HERRAMIENTAS:", [h.name for h in (await cliente.list_tools()).tools])
        for nombre, args in PRUEBAS:
            r = await cliente.call_tool(nombre, args)
            texto = " | ".join(b.text for b in r.content if hasattr(b, "text")).replace("\n", " ")
            print(f"\n{'⛔' if r.is_error else '✅'} {nombre}({args})\n   {texto[:150]}")

asyncio.run(main())
