from typing import List, Dict


def build_context(chunks: List[dict]) -> str:
    """
    Monta o contexto textual que será enviado para a IA.
    Inclui documento, item, título e texto.
    """
    partes = []

    for chunk in chunks:
        partes.append(
            f"Documento: {chunk.get('documento', 'N/A')}\n"
            f"Item: {chunk.get('item', 'N/A')}\n"
            f"Título: {chunk.get('titulo', 'N/A')}\n"
            f"Tipo da fonte: {chunk.get('tipo_fonte', 'N/A')}\n"
            f"Texto: {chunk.get('texto', '')}"
        )

    return "\n\n".join(partes)


def build_sources(chunks: List[dict]) -> List[dict]:
    """
    Converte os chunks encontrados para o formato esperado pelo frontend.
    """
    fontes = []

    for chunk in chunks:
        fontes.append(
            {
                "documento": chunk.get("documento", "Documento não informado"),
                "item": chunk.get("item"),
                "titulo": chunk.get("titulo"),
                "referencia": chunk.get("referencia", chunk.get("item")),
                "trecho": chunk.get("texto", "")[:500],
                "tipo_fonte": chunk.get("tipo_fonte"),
            }
        )

    return fontes


def build_local_response(pergunta: str, chunks: List[dict]) -> dict:
    """
    Gera uma resposta local forte, baseada nos trechos encontrados.
    Não depende de IA externa.
    """
    if not chunks:
        return {
            "resposta_objetiva": "Não encontrei base suficiente nos documentos carregados para responder com segurança.",
            "base_normativa_legal": "Base insuficiente no acervo atual.",
            "explicacao_pratica": "Refine a pergunta ou amplie a base documental.",
            "limite_tecnico": "Sem fonte suficiente, a resposta não pode ser conclusiva.",
            "fontes": [],
            "nivel_confianca": "Baixa",
        }

    principal = chunks[0]

    documento = principal.get("documento", "Documento não informado")
    item = principal.get("item", "Item não informado")
    titulo = principal.get("titulo", "Título não informado")
    texto = principal.get("texto", "")

    base_legal = f"{documento} — {item} — {titulo}"

    return {
        "resposta_objetiva": f"A base mais relacionada à sua pergunta está em {documento}, especialmente em {item}.",
        "base_normativa_legal": base_legal,
        "explicacao_pratica": texto,
        "limite_tecnico": "Resposta montada por recuperação textual estruturada dos documentos normativos carregados. Ainda sem interpretação avançada validada por IA externa.",
        "fontes": build_sources(chunks),
        "nivel_confianca": "Média",
    }


def merge_llm_with_sources(llm_data: dict, chunks: List[dict]) -> dict:
    """
    Injeta as fontes locais na resposta da IA.
    Garante que sempre haja consistência no retorno.
    """
    llm_data["fontes"] = build_sources(chunks)

    if "nivel_confianca" not in llm_data or not llm_data["nivel_confianca"]:
        llm_data["nivel_confianca"] = "Média"

    return llm_data