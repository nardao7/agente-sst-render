import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_chunks():
    chunks = []
    for file in DATA_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            chunks.extend(json.load(f))
    return chunks


def search_chunks(pergunta: str, limit: int = 5):
    pergunta_lower = pergunta.lower()
    all_chunks = load_chunks()

    scored = []
    for chunk in all_chunks:
        texto = chunk.get("texto", "").lower()
        score = 0

        for token in pergunta_lower.split():
            if token in texto:
                score += 1

        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:limit]]