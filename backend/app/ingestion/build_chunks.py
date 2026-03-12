import json
import re
from pathlib import Path
from typing import List
from pypdf import PdfReader

RAW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw_sources"
PROCESSED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed"


def ensure_dirs():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extrai texto de PDFs digitais.
    Para PDFs escaneados sem camada de texto, será necessário OCR em outra etapa.
    """
    reader = PdfReader(str(pdf_path))
    pages = []

    for page in reader.pages:
        pages.append(page.extract_text() or "")

    return "\n".join(pages)


def split_blocks_by_normative_pattern(text: str) -> List[str]:
    """
    Divide o texto em blocos usando padrões comuns:
    - NR-35.1
    - 35.1.1
    - Art. 1º
    - Anexo 9
    - NHO 01
    """
    pattern = r"(?=(?:NR-\d+(?:\.\d+)*|(?:\d+\.\d+(?:\.\d+)*)|Art\.\s*\d+º?|Anexo\s+\d+|NHO\s*\d+))"
    parts = re.split(pattern, text)
    return [p.strip() for p in parts if p.strip()]


def classify_source_type(path: Path) -> str:
    """
    Classifica a fonte com base na pasta.
    """
    if "nr" in path.parts:
        return "Norma Regulamentadora"
    if "nho" in path.parts:
        return "Norma de Higiene Ocupacional"
    if "leis" in path.parts:
        return "Base legal"
    return "Fonte normativa"


def infer_document_name(path: Path) -> str:
    """
    Gera um nome básico do documento a partir do nome do arquivo.
    """
    return path.stem.replace("_", " ").replace("-", " ").upper()


def infer_keywords(text: str) -> List[str]:
    """
    Extrai palavras-chave simples do início do texto.
    Pode ser refinado depois.
    """
    candidates = re.findall(r"[A-Za-zÀ-ÿ0-9\-]{4,}", text.lower())
    unique = []
    for word in candidates:
        if word not in unique:
            unique.append(word)
        if len(unique) >= 12:
            break
    return unique


def build_chunks_from_text(documento: str, tipo_fonte: str, text: str) -> List[dict]:
    """
    Converte o texto bruto em chunks estruturados.
    """
    blocks = split_blocks_by_normative_pattern(text)
    chunks = []

    for block in blocks:
        first_line = block.split("\n", 1)[0].strip()
        item = first_line[:120]
        titulo = first_line[:120]

        chunks.append(
            {
                "documento": documento,
                "item": item,
                "titulo": titulo,
                "referencia": item,
                "tipo_fonte": tipo_fonte,
                "palavras_chave": infer_keywords(block),
                "texto": block[:2500],
            }
        )

    return chunks


def process_pdf(pdf_path: Path):
    documento = infer_document_name(pdf_path)
    tipo_fonte = classify_source_type(pdf_path)
    text = extract_text_from_pdf(pdf_path)
    chunks = build_chunks_from_text(documento, tipo_fonte, text)

    out_file = PROCESSED_DIR / f"{pdf_path.stem}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


def main():
    ensure_dirs()

    pdf_files = list(RAW_DIR.rglob("*.pdf"))
    for pdf_file in pdf_files:
        print(f"Processando: {pdf_file}")
        process_pdf(pdf_file)

    print("Ingestão concluída.")


if __name__ == "__main__":
    main()