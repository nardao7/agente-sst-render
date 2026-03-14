import re
from unidecode import unidecode


def normalize(text: str) -> str:
    text = unidecode(text.lower().strip())
    text = re.sub(r"\s+", " ", text)
    return text


def classify_query_intent(pergunta: str) -> str:
    """
    Classifica a intenção principal da pergunta do usuário.

    Tipos:
    - norma_item: quer saber qual norma/item fala de algo
    - obrigacao: quer saber obrigação legal/normativa
    - conceito: quer definição ou conceito
    - pratica: quer explicação aplicada
    - programa: quer programa/documento obrigatório
    - insalubridade_periculosidade: quer enquadramento técnico
    - estudo: pergunta didática
    - geral: fallback
    """
    q = normalize(pergunta)

    if any(x in q for x in ["qual item", "qual norma", "qual nr", "onde diz", "onde fala", "qual anexo"]):
        return "norma_item"

    if any(x in q for x in ["é obrigatório", "obrigatorio", "deve", "precisa", "tem que", "responsabilidade", "obrigação", "obrigacao"]):
        return "obrigacao"

    if any(x in q for x in ["o que é", "oque é", "conceito", "definição", "definicao", "significa"]):
        return "conceito"

    if any(x in q for x in ["na prática", "na pratica", "como funciona", "como aplicar", "como faz", "como deve ser aplicado"]):
        return "pratica"

    if any(x in q for x in ["programa", "pgr", "pcmso", "ltcat", "laudo", "documento obrigatório", "documento obrigatorio"]):
        return "programa"

    if any(x in q for x in ["insalubridade", "periculosidade", "grau de insalubridade", "caracteriza insalubridade", "caracteriza periculosidade"]):
        return "insalubridade_periculosidade"

    if any(x in q for x in ["explique", "resuma", "me ensine", "atividade", "prova", "estudo"]):
        return "estudo"

    return "geral"