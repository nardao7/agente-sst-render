import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from app.schemas import AskRequest, AskResponse
from app.rag import search_chunks
from app.prompts import SYSTEM_PROMPT
from app.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_ENABLED

# --------------------------------------------------
# CRIAÇÃO DA API
# --------------------------------------------------

app = FastAPI(title="Agente SST API")

# --------------------------------------------------
# CORS
# Permite que o frontend hospedado no Render
# converse com o backend sem bloqueio do navegador
# --------------------------------------------------

origins = [
    "https://agente-sst-render-web.onrender.com",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# CLIENTE OPENAI
# Só cria se houver chave configurada
# --------------------------------------------------

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_ENABLED else None


# --------------------------------------------------
# FUNÇÕES AUXILIARES
# --------------------------------------------------

def montar_resposta_local(pergunta: str, encontrados: list) -> dict:
    """
    Gera uma resposta local segura sem depender da OpenAI.
    Essa função é usada como fallback para nunca quebrar a aplicação.
    """
    if not encontrados:
        return {
            "resposta_objetiva": "Não encontrei base suficiente nos documentos carregados para responder com segurança.",
            "base_normativa_legal": "Base insuficiente no acervo atual.",
            "explicacao_pratica": "Refine a pergunta ou amplie a base documental.",
            "limite_tecnico": "Sem fonte suficiente, a resposta não pode ser conclusiva.",
            "fontes": [],
            "nivel_confianca": "Baixa",
        }

    principal = encontrados[0]

    documento = principal.get("documento", "Documento não informado")
    referencia = principal.get("referencia", "Referência não informada")
    texto = principal.get("texto", "")

    return {
        "resposta_objetiva": f"A referência mais relacionada à sua pergunta é {documento}.",
        "base_normativa_legal": f"{documento} — {referencia}.",
        "explicacao_pratica": texto,
        "limite_tecnico": "Esta resposta foi montada a partir da busca textual nos documentos carregados, com fallback local sem interpretação aprofundada por IA.",
        "fontes": [
            {
                "documento": item.get("documento", "Documento não informado"),
                "referencia": item.get("referencia", "Referência não informada"),
                "trecho": item.get("texto", "")[:300],
            }
            for item in encontrados
        ],
        "nivel_confianca": "Média" if encontrados else "Baixa",
    }


def montar_contexto(encontrados: list) -> str:
    """
    Junta os trechos encontrados em um bloco de contexto
    para enviar ao modelo da OpenAI.
    """
    return "\n\n".join(
        [
            f"Documento: {c.get('documento')}\n"
            f"Referencia: {c.get('referencia')}\n"
            f"Texto: {c.get('texto')}"
            for c in encontrados
        ]
    )


def tentar_resposta_openai(pergunta: str, encontrados: list) -> dict:
    """
    Tenta gerar uma resposta com OpenAI.
    Se qualquer coisa falhar, levanta exceção e o sistema cai no fallback local.
    """
    if not OPENAI_ENABLED or client is None:
        raise RuntimeError("OpenAI não configurada.")

    contexto = montar_contexto(encontrados)

    if not contexto.strip():
        raise RuntimeError("Sem contexto suficiente para IA.")

    prompt_user = f"""
Pergunta do usuário:
{pergunta}

Fontes recuperadas:
{contexto}

Responda em JSON válido com as chaves:
resposta_objetiva
base_normativa_legal
explicacao_pratica
limite_tecnico
nivel_confianca
"""

    # Chamada à OpenAI
    response = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_user},
        ],
    )

    texto = response.output_text.strip()

    # Tenta transformar a resposta em JSON
    data = json.loads(texto)

    # Injeta as fontes encontradas pelo motor local
    data["fontes"] = [
        {
            "documento": item.get("documento", "Documento não informado"),
            "referencia": item.get("referencia", "Referência não informada"),
            "trecho": item.get("texto", "")[:300],
        }
        for item in encontrados
    ]

    # Se o modelo esquecer o campo, adicionamos default
    if "nivel_confianca" not in data:
        data["nivel_confianca"] = "Média"

    return data


# --------------------------------------------------
# ROTAS
# --------------------------------------------------

@app.get("/")
def root():
    return {"message": "Agente SST online"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/debug/openai")
def debug_openai():
    """
    Rota simples para verificar se o backend está vendo
    a OpenAI como habilitada.
    """
    return {
        "openai_enabled": OPENAI_ENABLED,
        "model": OPENAI_MODEL,
        "api_key_configured": bool(OPENAI_API_KEY),
    }


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """
    Fluxo principal:
    1. busca contexto local
    2. tenta OpenAI
    3. se falhar, devolve fallback local
    """
    encontrados = search_chunks(req.pergunta, limit=5)

    try:
        return tentar_resposta_openai(req.pergunta, encontrados)
    except Exception as error:
        print("FALLBACK LOCAL ATIVADO:", str(error))
        return montar_resposta_local(req.pergunta, encontrados)