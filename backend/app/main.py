from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import AskRequest, AskResponse
from app.prompts import SYSTEM_PROMPT
from app.rag import search_chunks
from app.response_builder import (
    build_context,
    build_local_response,
    merge_llm_with_sources,
)
from app.config import AI_PROVIDER
from app.providers.provider_gemini import GeminiProvider
from app.providers.provider_openai import OpenAIProvider

app = FastAPI(title="Agente SST API")

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

gemini_provider = GeminiProvider()
openai_provider = OpenAIProvider()


def get_provider_chain():
    if AI_PROVIDER == "openai":
        return [openai_provider, gemini_provider]
    return [gemini_provider, openai_provider]


@app.get("/")
def root():
    return {"message": "Agente SST online"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/debug/providers")
def debug_providers():
    return {
        "main_provider": AI_PROVIDER,
        "gemini_available": gemini_provider.is_available(),
        "openai_available": openai_provider.is_available(),
    }


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    encontrados = search_chunks(req.pergunta, limit=5)

    if not encontrados:
        return build_local_response(req.pergunta, [])

    contexto = build_context(encontrados)

    for provider in get_provider_chain():
        if not provider.is_available():
            continue

        try:
            llm_data = provider.generate_structured_response(
                pergunta=req.pergunta,
                contexto=contexto,
                system_prompt=SYSTEM_PROMPT,
            )
            return merge_llm_with_sources(llm_data, encontrados, provider.__class__.__name__)
        except Exception as error:
            print(f"PROVIDER FAILED: {provider.__class__.__name__} -> {str(error)}")
            continue

    return build_local_response(req.pergunta, encontrados)