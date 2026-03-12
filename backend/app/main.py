from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import AskRequest, AskResponse
from app.rag import search_chunks

# Cria a aplicação principal da API
app = FastAPI(title="Agente SST API")

# Libera o frontend publicado no Render e também localhost para testes locais
origins = [
    "https://agente-sst-render-web.onrender.com",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Agente SST online"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """
    Esta versão não usa OpenAI.
    Ela responde somente com base nos JSONs carregados.
    É ideal para estabilizar o projeto e confirmar
    que backend + frontend + Render estão funcionando.
    """
    encontrados = search_chunks(req.pergunta, limit=5)

    # Se não encontrar nada relevante, retorna resposta segura
    if not encontrados:
        return {
            "resposta_objetiva": "Não encontrei base suficiente nos documentos carregados para responder com segurança.",
            "base_normativa_legal": "Base insuficiente no acervo atual.",
            "explicacao_pratica": "Refine a pergunta ou amplie a base documental.",
            "limite_tecnico": "Sem fonte suficiente, a resposta não pode ser conclusiva.",
            "fontes": [],
            "nivel_confianca": "Baixa",
        }

    # Usa o primeiro trecho encontrado como base principal
    principal = encontrados[0]

    documento = principal.get("documento", "Documento não informado")
    referencia = principal.get("referencia", "Referência não informada")
    texto = principal.get("texto", "")

    return {
        "resposta_objetiva": f"A referência mais relacionada à sua pergunta é {documento}.",
        "base_normativa_legal": f"{documento} — {referencia}.",
        "explicacao_pratica": texto,
        "limite_tecnico": "Esta resposta foi montada a partir da busca textual nos documentos carregados, sem interpretação avançada por IA.",
        "fontes": [
            {
                "documento": item.get("documento", "Documento não informado"),
                "referencia": item.get("referencia", "Referência não informada"),
                "trecho": item.get("texto", "")[:300],
            }
            for item in encontrados
        ],
        "nivel_confianca": "Média",
    }