from typing import List
from app.query_intent import classify_query_intent

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
    Converte os chunks para o formato do frontend.
    Limita a 3 fontes principais para evitar excesso.
    """
    fontes = []

    for chunk in chunks[:3]:
        fontes.append(
            {
                "documento": chunk.get("documento", "Documento não informado"),
                "item": chunk.get("item"),
                "titulo": chunk.get("titulo"),
                "referencia": chunk.get("referencia", chunk.get("item")),
                "trecho": chunk.get("texto", "")[:350],
                "tipo_fonte": chunk.get("tipo_fonte"),
            }
        )

    return fontes


def build_local_response(pergunta: str, chunks: List[dict]) -> dict:
    """
    Gera resposta local forte, adaptada ao tipo da pergunta.
    """
    intent = classify_query_intent(pergunta)

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

    if intent == "norma_item":
        resposta_objetiva = f"A base mais relacionada à sua pergunta está em {documento}, especialmente no item {item}."
        explicacao_pratica = f"O item recuperado trata de {titulo.lower()}."
    elif intent == "obrigacao":
        resposta_objetiva = f"A obrigação mais relacionada à sua pergunta está prevista em {documento}, no item {item}."
        explicacao_pratica = f"O trecho normativo indica obrigação ligada a {titulo.lower()}."
    elif intent == "conceito":
        resposta_objetiva = f"O conceito mais relacionado à sua pergunta aparece em {documento}, item {item}."
        explicacao_pratica = f"O trecho recuperado apresenta a definição ou caracterização normativa de {titulo.lower()}."
    elif intent == "pratica":
        resposta_objetiva = f"A orientação normativa mais relacionada ao tema está em {documento}, item {item}."
        explicacao_pratica = f"Na prática, o trecho recuperado indica como o tema deve ser entendido ou aplicado em SST."
    elif intent == "programa":
        resposta_objetiva = f"O programa ou documento mais relacionado ao tema aparece em {documento}, item {item}."
        explicacao_pratica = f"O trecho recuperado aponta relação normativa com {titulo.lower()}."
    elif intent == "insalubridade_periculosidade":
        resposta_objetiva = f"A base mais relacionada ao tema de insalubridade/periculosidade está em {documento}, item {item}."
        explicacao_pratica = "Esse tipo de tema exige leitura cuidadosa do item, anexos e, quando aplicável, avaliação técnica no ambiente real."
    else:
        resposta_objetiva = f"A base mais relacionada à sua pergunta está em {documento}, especialmente no item {item}."
        explicacao_pratica = f"O trecho recuperado trata do tema em {documento}, com foco em {titulo.lower()}."

    return {
        "resposta_objetiva": resposta_objetiva,
        "base_normativa_legal": f"{documento} — {item} — {titulo}",
        "explicacao_pratica": explicacao_pratica,
        "limite_tecnico": (
            "Resposta baseada em recuperação textual direta da base normativa carregada. "
            "A interpretação final depende do contexto completo da norma e da situação concreta."
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