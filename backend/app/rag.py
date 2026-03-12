import json
import re
from pathlib import Path
from typing import List
from unidecode import unidecode

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def normalize_text(text: str) -> str:
    text = unidecode(text.lower().strip())
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize(text: str) -> List[str]:
    text = normalize_text(text)
    return re.findall(r"[a-z0-9\-]+", text)


def load_chunks() -> List[dict]:
    chunks = []
    for file in DATA_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            chunks.extend(json.load(f))
    return chunks


def score_chunk(query_tokens: List[str], chunk: dict) -> int:
    score = 0

    documento = normalize_text(chunk.get("documento", ""))
    item = normalize_text(chunk.get("item", ""))
    titulo = normalize_text(chunk.get("titulo", ""))
    texto = normalize_text(chunk.get("texto", ""))
    palavras_chave = " ".join(chunk.get("palavras_chave", []))
    palavras_chave = normalize_text(palavras_chave)

    for token in query_tokens:
        if token in documento:
            score += 6
        if token in item:
            score += 6
        if token in titulo:
            score += 5
        if token in palavras_chave:
            score += 4
        if token in texto:
            score += 1

    return score


def search_chunks(pergunta: str, limit: int = 5) -> List[dict]:
    query_tokens = tokenize(pergunta)
    all_chunks = load_chunks()

    scored = []
    for chunk in all_chunks:
        score = score_chunk(query_tokens, chunk)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:limit]]