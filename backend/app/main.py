import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from app.schemas import AskRequest, AskResponse
from app.rag import search_chunks
from app.prompts import SYSTEM_PROMPT
from app.config import OPENAI_API_KEY, OPENAI_MODEL

# Cria a aplicação principal da API
app = FastAPI(title="Agente SST API")

# Libera o frontend para acessar o backend
# Nesta fase inicial, usamos "*" para permitir testes de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria o cliente da OpenAI usando a chave armazenada no Render
client = OpenAI(api_key=OPENAI_API_KEY)


@app.get("/")
def root():
    return {"message": "Agente SST online"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    encontrados = search_chunks(req.pergunta, limit=5)

    contexto = "\n\n".join(
        [
            f"Documento: {c.get('documento')}\n"
            f"Referencia: {c.get('referencia')}\n"
            f"Texto: {c.get('texto')}"
            for c in encontrados
        ]
    )

    # Se não achar nada relevante nos arquivos JSON
    if not contexto.strip():
        return {
            "resposta_objetiva": "Não encontrei base suficiente nos documentos carregados para responder com segurança.",
            "base_normativa_legal": "Base insuficiente no acervo atual.",
            "explicacao_pratica": "É necessário ampliar a base documental ou refinar a pergunta.",
            "limite_tecnico": "Sem fonte suficiente, a resposta não pode ser conclusiva.",
            "fontes": [],
            "nivel_confianca": "Baixa",
        }

    prompt_user = f"""
Pergunta do usuário:
{req.pergunta}

Fontes recuperadas:
{contexto}

Responda em JSON válido com as chaves:
resposta_objetiva
base_normativa_legal
explicacao_pratica
limite_tecnico
nivel_confianca
"""

    resp = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_user},
        ],
    )

    content = resp.output_text.strip()

    try:
        data = json.loads(content)
    except Exception:
        data = {
            "resposta_objetiva": "Houve falha ao interpretar a resposta do modelo.",
            "base_normativa_legal": "Resposta do modelo não retornou JSON válido.",
            "explicacao_pratica": "Verifique o prompt ou o retorno do modelo.",
            "limite_tecnico": "A resposta não pôde ser estruturada corretamente.",
            "nivel_confianca": "Baixa",
        }

    data["fontes"] = [
        {
            "documento": c.get("documento"),
            "referencia": c.get("referencia"),
            "trecho": c.get("texto", "")[:300],
        }
        for c in encontrados
    ]

    return data