import json
import re
from pathlib import Path
from typing import List
from unidecode import unidecode

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


# -----------------------------------------
# MAPA DE SINÔNIMOS E TERMOS RELACIONADOS
# -----------------------------------------
# Isso ajuda o sistema a entender perguntas diferentes
# que querem dizer a mesma coisa.
SEMANTIC_HINTS = {
    "epi": [
        "equipamento de proteção individual",
        "equipamento de protecao individual",
        "proteção individual",
        "protecao individual",
        "uso de epi",
        "nr 06",
        "nr-06",
        "ca",
        "certificado de aprovação",
    ],
    "trabalho em altura": [
        "altura",
        "nr 35",
        "nr-35",
        "trabalho em altura",
    ],
    "insalubridade": [
        "nr 15",
        "nr-15",
        "atividades insalubres",
        "anexo 9",
        "frio",
        "agentes biológicos",
        "agentes biologicos",
    ],
    "pcmso": [
        "nr 07",
        "nr-07",
        "programa de controle médico de saúde ocupacional",
        "programa de controle medico de saude ocupacional",
    ],
    "pgr": [
        "gro",
        "gerenciamento de riscos",
        "gerenciamento de riscos ocupacionais",
        "nr 01",
        "nr-01",
        "programa de gerenciamento de riscos",
    ],
}


def normalize_text(text: str) -> str:
    """
    Normaliza o texto:
    - minúsculas
    - sem acentos
    - sem excesso de espaços
    """
    text = unidecode(text.lower().strip())
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize(text: str) -> List[str]:
    """
    Quebra o texto em tokens simples.
    """
    text = normalize_text(text)
    return re.findall(r"[a-z0-9\-]+", text)


def expand_query(pergunta: str) -> List[str]:
    """
    Expande a pergunta com termos equivalentes.
    Isso faz o sistema entender melhor perguntas formuladas
    de jeitos diferentes.
    """
    pergunta_normalizada = normalize_text(pergunta)
    termos = [pergunta_normalizada]

    for chave, relacionados in SEMANTIC_HINTS.items():
        if chave in pergunta_normalizada:
            termos.extend(relacionados)

        for relacionado in relacionados:
            if relacionado in pergunta_normalizada:
                termos.append(chave)
                termos.extend(relacionados)

    tokens = []
    for termo in termos:
        tokens.extend(tokenize(termo))

    # remove duplicados mantendo ordem
    unicos = []
    for token in tokens:
        if token not in unicos:
            unicos.append(token)

    return unicos


def load_chunks() -> List[dict]:
    """
    Carrega todos os JSONs processados.
    """
    chunks = []
    for file in DATA_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            chunks.extend(json.load(f))
    return chunks


def score_chunk(query_tokens: List[str], chunk: dict) -> int:
    """
    Pontua cada chunk.
    Critérios:
    - documento, item e título valem mais
    - palavras-chave ajudam bastante
    - texto vale menos
    - fontes principais (NR/NHO/Base legal) ganham prioridade
    - materiais auxiliares ganham menos peso
    """
    score = 0

    documento = normalize_text(chunk.get("documento", ""))
    item = normalize_text(chunk.get("item", ""))
    titulo = normalize_text(chunk.get("titulo", ""))
    texto = normalize_text(chunk.get("texto", ""))
    palavras_chave = " ".join(chunk.get("palavras_chave", []))
    palavras_chave = normalize_text(palavras_chave)
    tipo_fonte = normalize_text(chunk.get("tipo_fonte", ""))

    for token in query_tokens:
        if token in documento:
            score += 8
        if token in item:
            score += 8
        if token in titulo:
            score += 6
        if token in palavras_chave:
            score += 5
        if token in texto:
            score += 1

    # pesos por tipo de fonte
    if "norma regulamentadora" in tipo_fonte:
        score += 8
    elif "anexo de norma regulamentadora" in tipo_fonte:
        score += 7
    elif "norma de higiene ocupacional" in tipo_fonte:
        score += 7
    elif "base legal" in tipo_fonte:
        score += 5
    elif "norma complementar" in tipo_fonte:
        score += 3
    elif "material auxiliar" in tipo_fonte:
        score += 1

    return score


def deduplicate_chunks(chunks: List[dict]) -> List[dict]:
    """
    Remove chunks duplicados ou muito parecidos pelo par
    documento + item + início do texto.
    """
    vistos = set()
    resultado = []

    for chunk in chunks:
        chave = (
            chunk.get("documento", ""),
            chunk.get("item", ""),
            chunk.get("texto", "")[:120],
        )
        if chave not in vistos:
            vistos.add(chave)
            resultado.append(chunk)

    return resultado


def search_chunks(pergunta: str, limit: int = 5) -> List[dict]:
    """
    Busca os chunks mais relevantes para a pergunta.
    """
    query_tokens = expand_query(pergunta)
    all_chunks = load_chunks()

    scored = []
    for chunk in all_chunks:
        score = score_chunk(query_tokens, chunk)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)

    chunks_ordenados = [item[1] for item in scored]
    chunks_ordenados = deduplicate_chunks(chunks_ordenados)

    return chunks_ordenados[:limit]