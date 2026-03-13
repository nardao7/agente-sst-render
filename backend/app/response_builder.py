from typing import List


def build_context(chunks: List[dict]) -> str:
    """
    Monta o contexto para a IA.
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
    Converte os chunks para o formato que o frontend entende.
    """
    return [
        {
            "documento": chunk.get("documento", "Documento não informado"),
            "item": chunk.get("item"),
            "titulo": chunk.get("titulo"),
            "referencia": chunk.get("referencia", chunk.get("item")),
            "trecho": chunk.get("texto", "")[:450],
            "tipo_fonte": chunk.get("tipo_fonte"),
        }
        for chunk in chunks[:3]
    ]


def build_local_response(pergunta: str, chunks: List[dict]) -> dict:
    """
    Resposta local mais forte e menos genérica.
    """
    if not chunks:
        return {
            "resposta_objetiva": "Não encontrei base suficiente nos documentos carregados para responder com segurança.",
            "base_normativa_legal": "Base insuficiente no acervo atual.",
            "explicacao_pratica": "Refine a pergunta ou amplie a base documental.",
            "limite_tecnico": "Sem fonte suficiente, a resposta não pode ser conclusiva.",
            "trecho_normativo_exato": "Nenhum trecho normativo encontrado.",
            "fontes": [],
            "nivel_confianca": "Baixa",
            "modo_resposta": "fallback_local",
        }

    principal = chunks[0]

    documento = principal.get("documento", "Documento não informado")
    item = principal.get("item", "Item não informado")
    titulo = principal.get("titulo", "Título não informado")
    texto = principal.get("texto", "")

    return {
        "resposta_objetiva": f"A norma mais relacionada ao tema perguntado é {documento}, especialmente no item {item}.",
        "base_normativa_legal": f"{documento} — {item} — {titulo}",
        "explicacao_pratica": (
            f"De forma prática, o trecho recuperado indica que o tema consultado está tratado em {documento}, "
            f"no item {item}, com foco em {titulo.lower()}."
        ),
        "limite_tecnico": (
            "Resposta baseada em recuperação textual direta. A interpretação depende do contexto completo da norma e da situação real de trabalho."
        ),
        "trecho_normativo_exato": texto,
        "fontes": build_sources(chunks),
        "nivel_confianca": "Alta" if "norma regulamentadora" in str(principal.get("tipo_fonte", "")).lower() else "Média",
        "modo_resposta": "fallback_local",
    }


def merge_llm_with_sources(llm_data: dict, chunks: List[dict], provider_name: str) -> dict:
    """
    Injeta fontes e campos obrigatórios na resposta da IA.
    """
    llm_data["fontes"] = build_sources(chunks)

    if "trecho_normativo_exato" not in llm_data or not llm_data["trecho_normativo_exato"]:
        llm_data["trecho_normativo_exato"] = chunks[0].get("texto", "") if chunks else ""

    if "nivel_confianca" not in llm_data or not llm_data["nivel_confianca"]:
        llm_data["nivel_confianca"] = "Média"

    llm_data["modo_resposta"] = provider_name
    return llm_data