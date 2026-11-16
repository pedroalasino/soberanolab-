# 1) La base: un Linux chiquito con Python 3.11
FROM python:3.11-slim
WORKDIR /app

# 2) Primero las librerías (Docker las reusa si no cambian)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) Después el motor: código, fichas, documentos y página
COPY . .

# 4) Seguridad: no correr como administrador adentro de la caja
RUN useradd --create-home soberai && chown -R soberai /app
USER soberai

# 5) Ollama queda afuera, en tu compu
ENV OLLAMA_URL=http://host.docker.internal:11434

# 6) Puerto, chequeo de salud y cómo se prende
EXPOSE 8001
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/salud')"
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]