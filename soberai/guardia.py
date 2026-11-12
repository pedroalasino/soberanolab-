import re

import config

TRAMPA = re.compile(
    r"ignor[aá]|olvid[aá] (tus|las) (reglas|instrucciones)|system prompt|prompt del sistema|"
    r"revel[aá] (tus|las) instrucciones|actu[aá] como|sos ahora|modo desarrollador|jailbreak",
    re.IGNORECASE)
SALUDO = re.compile(r"^\s*(hola|buenas|buen d[ií]a|buenas tardes|buenas noches|hey)[\s!.,]*$", re.IGNORECASE)
SECRETO = re.compile(r"(sk-[A-Za-z0-9]{10,}|AIza[0-9A-Za-z_-]{20,}|lsv2_[A-Za-z0-9_]{10,}|AQ\.[A-Za-z0-9_-]{10,})")

def revisar_entrada(mensaje, ficha):
    """Antes del modelo. Devuelve una respuesta fija, o None si el mensaje puede pasar."""
    mensaje = (mensaje or "").strip()
    if not mensaje:
        return "No recibí ningún mensaje. ¿En qué te ayudo?"
    if len(mensaje) > config.MAX_LARGO:
        return f"El mensaje es muy largo. Escribilo en menos de {config.MAX_LARGO} caracteres."
    if TRAMPA.search(mensaje):
        return f"No puedo hacer eso. Este asistente {ficha.descripcion[0].lower() + ficha.descripcion[1:]}."
    if SALUDO.match(mensaje):
        return f"¡Hola! Soy el asistente {ficha.nombre}. {ficha.descripcion}. ¿Qué necesitás?"
    return None

def revisar_salida(respuesta):
    """Después del modelo. Nunca deja salir algo que parezca una clave."""
    return SECRETO.sub("[dato oculto]", respuesta or "").strip()
