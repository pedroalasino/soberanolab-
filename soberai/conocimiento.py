import math
import re
import sys

from rank_bm25 import BM25Okapi

import config

PALABRAS_VACIAS = {"qué", "que", "cuál", "cómo", "dónde", "cuándo", "quién", "de", "del", "la", "el",
                   "los", "las", "un", "una", "con", "en", "y", "o", "a", "por", "para", "su", "sus",
                   "se", "es", "son", "hay", "tiene", "hace", "hizo", "sabe", "usa", "me", "lo", "le"}

def palabras(texto):
    return re.findall(r"[a-záéíóúñü0-9]+(?:\.[a-záéíóúñü0-9]+)*", texto.lower())

def claves(texto):
    return [p for p in palabras(texto) if p not in PALABRAS_VACIAS and len(p) > 2]

def cargar_bloques(agente):
    bloques = []
    for archivo in sorted((config.CARPETA / "conocimiento" / agente).glob("*.*")):
        texto = archivo.read_text(encoding="utf-8-sig")
        separador = r"\n(?=## )" if archivo.suffix == ".md" else r"\n\s*\n"
        for parte in re.split(separador, texto):
            parte = parte.replace("## ", "").strip()
            if parte and not parte.startswith("# "):
                bloques.append({"fuente": archivo.name, "texto": parte})
    return bloques

def coseno(a, b):
    num = sum(x * y for x, y in zip(a, b))
    return num / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)) or 1)

class BaseDeConocimiento:
    def __init__(self, agente, usar_vectores=True):
        self.bloques = cargar_bloques(agente)
        self.bm25 = BM25Okapi([palabras(b["texto"]) for b in self.bloques], b=0.3)  # b bajo: no castiga tanto los bloques largos
        self.vocabulario = {p for b in self.bloques for p in palabras(b["texto"])}
        self.emb, self.vectores = None, []
        if usar_vectores:
            try:
                from langchain_ollama import OllamaEmbeddings
                self.emb = OllamaEmbeddings(model=config.modelo("embeddings"), base_url=config.OLLAMA_URL)
                self.vectores = self.emb.embed_documents([b["texto"] for b in self.bloques])
            except Exception as error:
                print(f"[conocimiento] Sin vectores para {agente} ({error.__class__.__name__}): uso solo BM25.", file=sys.stderr)
                self.emb = None

    def buscar(self, consulta, k=3):
        c = claves(consulta)
        puntos_bm25 = self.bm25.get_scores(c) if c else [0] * len(self.bloques)
        ranking_bm25 = [i for i in sorted(range(len(self.bloques)), key=lambda i: -puntos_bm25[i]) if puntos_bm25[i] > 0]
        ranking_vec, mejor_sim = [], 0
        if self.emb:
            v = self.emb.embed_query(consulta)
            sims = [coseno(v, x) for x in self.vectores]
            ranking_vec = sorted(range(len(self.bloques)), key=lambda i: -sims[i])
            mejor_sim = sims[ranking_vec[0]]
        if not any(p in self.vocabulario for p in c) and mejor_sim < 0.6:
            return []  # umbral: nada que ver con los documentos
        puntos = {}
        for ranking in (ranking_bm25, ranking_vec):
            for pos, i in enumerate(ranking):
                puntos[i] = puntos.get(i, 0) + 1 / (60 + pos)  # RRF
        return [self.bloques[i] for i in sorted(puntos, key=lambda i: -puntos[i])[:k]]

_bases = {}

def base(agente, usar_vectores=True):
    if agente not in _bases:
        _bases[agente] = BaseDeConocimiento(agente, usar_vectores)
    return _bases[agente]
