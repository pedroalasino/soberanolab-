# SOBERAI · motor de IA de SoberanoLab

Infraestructura propia de producción de IA: corre en tu servidor con Ollama, sin servicios de terceros.
Sobre el motor corren agentes configurables; cada uno tiene su ficha, sus documentos y sus herramientas permitidas.

## Qué incluye

| Pieza | Archivo | Qué hace |
|---|---|---|
| Registro de modelos | `config.py` | El motor pide un rol (chat, respaldo, embeddings); el modelo se cambia por variable de entorno |
| Router de modelos | `router.py` | Usa el modelo titular y, si falla, el de respaldo |
| Agentes configurables | `agentes/*.json`, `agentes.py` | Cada agente es una ficha validada con Pydantic |
| Conocimiento | `conocimiento.py`, `conocimiento/<agente>/` | RAG híbrido por agente: BM25 + vectores + RRF + umbral de relevancia |
| Herramientas | `herramientas.py` | Function calling con permisos por agente |
| Guardrails | `guardia.py` | Frena prompt injection y mensajes gigantes; tapa claves en las respuestas |
| Orquestador | `motor.py` | LangGraph: guardia → agente ReAct con tope de pasos y memoria por agente y sesión |
| API gateway | `api.py` | FastAPI con API key por cliente, límite por minuto y streaming |
| Página pública | `web/` | Chat para cualquier visitante, con límite por persona |
| Observabilidad | `observabilidad.py` | Latencia, tokens, herramientas y errores; no guarda el texto del usuario |
| Evaluación | `evaluar.py` | Examen automático por agente; si baja la nota, no se publica |
| Tests | `test_soberai.py` | 18 pruebas de las reglas fijas, sin IA |
| MCP | `servidor_mcp.py` | Expone el motor con herramientas de solo lectura |

## Cómo correrlo

Necesitás [Ollama](https://ollama.com) con `qwen2.5:3b` y `nomic-embed-text`.

```bash
pip install -r requirements.txt
uvicorn api:app --port 8001      # página en http://localhost:8001
python -m pytest -v              # tests sin IA
python evaluar.py                # examen de los agentes (usa el modelo)
python probar_mcp.py             # prueba del servidor MCP
```

Para clientes con clave propia: `SOBERAI_CLIENTES='{"clave-larga": ["portfolio"]}'`.
Para cambiar de modelo: `SOBERAI_CHAT=qwen2.5:7b`.
