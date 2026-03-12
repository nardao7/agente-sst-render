from typing import List


def build_context(chunks: List[dict]) -> str:
    """
    Monta o contexto enviado ao provedor de IA.
    Inclui documento, item, título, tipo e texto.
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
    Converte os chunks para o formato de fontes do frontend.
    """
    return [
        {
            "documento": chunk.get("documento", "Documento não informado"),
            "item": chunk.get("item"),
            "titulo": chunk.get("titulo"),
            "referencia": chunk.get("referencia", chunk.get("item")),
            "trecho": chunk.get("texto", "")[:700],
            "tipo_fonte": chunk.get("tipo_fonte"),
        }
        for chunk in chunks
    ]


def build_local_response(pergunta: str, chunks: List[dict]) -> dict:
    """
    Resposta local confiável.
    Usa o chunk principal como base da citação normativa.
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
        "resposta_objetiva": f"A base mais relacionada à sua pergunta está em {documento}, especialmente em {item}.",
        "base_normativa_legal": f"{documento} — {item} — {titulo}",
        "explicacao_pratica": (
            f"Com base no trecho identificado em {documento}, o tema tratado na sua pergunta "
            f"está diretamente ligado a {titulo.lower()}."
        ),
        "limite_tecnico": (
            "Resposta montada por recuperação textual estruturada dos documentos normativos carregados. "
            "Sem interpretação jurídica aprofundada e sem inferência além do trecho recuperado."
        ),
        "trecho_normativo_exato": texto,
        "fontes": build_sources(chunks),
        "nivel_confianca": "Média",
        "modo_resposta": "fallback_local",
    }


def merge_llm_with_sources(llm_data: dict, chunks: List[dict], provider_name: str) -> dict:
    """
    Injeta fontes e campos obrigatórios na resposta do provedor de IA.
    """
    llm_data["fontes"] = build_sources(chunks)

    if "trecho_normativo_exato" not in llm_data or not llm_data["trecho_normativo_exato"]:
        llm_data["trecho_normativo_exato"] = chunks[0].get("texto", "") if chunks else ""

    if "nivel_confianca" not in llm_data or not llm_data["nivel_confianca"]:
        llm_data["nivel_confianca"] = "Média"

    llm_data["modo_resposta"] = provider_name

    return llm_data