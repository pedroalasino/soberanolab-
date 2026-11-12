import sys

from langchain_ollama import ChatOllama

import config

def crear_llm(rol):
    return ChatOllama(
        model=config.modelo(rol),
        base_url=config.OLLAMA_URL,
        temperature=0,
        client_kwargs={"timeout": 60},
    )

def invocar(mensajes, herramientas=None):
    ultimo_error = None
    for rol in ["chat", "respaldo"]:
        llm = crear_llm(rol)
        if herramientas:
            llm = llm.bind_tools(herramientas)
        try:
            return llm.invoke(mensajes)
        except Exception as error:
            print(f"[router] Falló {config.modelo(rol)}: {error.__class__.__name__}. Pruebo el siguiente.", file=sys.stderr)
            ultimo_error = error
    raise ultimo_error
