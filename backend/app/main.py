# Importa o módulo json da biblioteca padrão do Python.
# Ele será usado para converter texto JSON em dicionário Python.
import json

# Importa a classe FastAPI, usada para criar a aplicação web/API.
from fastapi import FastAPI

# Importa o cliente oficial da OpenAI, que será usado para chamar o modelo.
from openai import OpenAI

# Importa os modelos de dados (schemas) usados na entrada e saída da rota /ask.
# AskRequest = formato esperado da pergunta recebida
# AskResponse = formato esperado da resposta retornada
from app.schemas import AskRequest, AskResponse

# Importa a função responsável por buscar trechos relevantes no acervo/RAG.
from app.rag import search_chunks

# Importa o prompt de sistema, que orienta o comportamento do modelo.
from app.prompts import SYSTEM_PROMPT

# Importa configurações do projeto:
# OPENAI_API_KEY = chave da API
# OPENAI_MODEL = modelo configurado para uso
from app.config import OPENAI_API_KEY, OPENAI_MODEL

# Cria a aplicação FastAPI e define um título para aparecer na documentação automática.
app = FastAPI(title="Agente SST API")

# Cria uma instância do cliente OpenAI usando a chave configurada no projeto.
client = OpenAI(api_key=OPENAI_API_KEY)


# Define uma rota GET para a raiz da API: "/"
# Serve para testar rapidamente se a aplicação está online.
@app.get("/")
def root():
    # Retorna uma mensagem simples em formato JSON.
    return {"message": "Agente SST online"}


# Define uma rota GET para "/health"
# Essa rota é normalmente usada por serviços de monitoramento para verificar se a API está saudável.
@app.get("/health")
def health():
    # Retorna um status simples.
    return {"status": "ok"}


# Define uma rota POST chamada "/ask"
# Ela recebe uma pergunta no formato AskRequest
# e devolve uma resposta estruturada no formato AskResponse.
@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    # Faz a busca dos trechos mais relevantes no acervo com base na pergunta do usuário.
    # O limit=5 indica que vamos buscar até 5 trechos.
    encontrados = search_chunks(req.pergunta, limit=5)

    # Monta um grande bloco de texto chamado "contexto"
    # juntando os documentos encontrados para enviar ao modelo.
    contexto = "\n\n".join(
        [
            # Para cada trecho encontrado, monta um texto com:
            # nome do documento, referência e conteúdo textual
            f"Documento: {c.get('documento')}\n"
            f"Referencia: {c.get('referencia')}\n"
            f"Texto: {c.get('texto')}"
            for c in encontrados
        ]
    )

    # Verifica se o contexto ficou vazio ou sem conteúdo útil.
    # Se não houver base documental suficiente, a API devolve uma resposta segura.
    if not contexto.strip():
        return {
            "resposta_objetiva": "Não encontrei base suficiente nos documentos carregados para responder com segurança.",
            "base_normativa_legal": "Base insuficiente no acervo atual.",
            "explicacao_pratica": "É necessário ampliar a base documental ou refinar a pergunta.",
            "limite_tecnico": "Sem fonte suficiente, a resposta não pode ser conclusiva.",
            "fontes": [],
            "nivel_confianca": "Baixa",
        }

    # Monta o prompt do usuário que será enviado ao modelo.
    # Aqui entram:
    # 1) a pergunta do usuário
    # 2) as fontes recuperadas pelo RAG
    # 3) a instrução para devolver JSON com chaves específicas
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

    # Faz a chamada ao modelo da OpenAI.
    # Usa o modelo definido em OPENAI_MODEL
    # e envia duas mensagens:
    # - system: com as regras gerais do agente
    # - user: com a pergunta e o contexto encontrado
    resp = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_user},
        ],
    )

    # Extrai o texto final retornado pelo modelo e remove espaços extras no início/fim.
    content = resp.output_text.strip()

    # Tenta converter a resposta do modelo em JSON/dicionário Python.
    # Isso é necessário porque pedimos que o modelo responda em JSON válido.
    try:
        data = json.loads(content)

    # Se a conversão falhar, significa que o modelo não devolveu JSON válido.
    # Nesse caso, montamos uma resposta padrão de erro controlado.
    except Exception:
        data = {
            "resposta_objetiva": "Houve falha ao interpretar a resposta do modelo.",
            "base_normativa_legal": "Resposta do modelo não retornou JSON válido.",
            "explicacao_pratica": "Verifique o prompt ou o retorno do modelo.",
            "limite_tecnico": "A resposta não pôde ser estruturada corretamente.",
            "nivel_confianca": "Baixa",
        }

    # Adiciona manualmente a lista de fontes à resposta final.
    # Isso garante que o retorno sempre inclua os trechos usados como base.
    data["fontes"] = [
        {
            # Nome do documento de origem
            "documento": c.get("documento"),

            # Referência do trecho/item/norma
            "referencia": c.get("referencia"),

            # Recorta os primeiros 300 caracteres do trecho para não devolver texto grande demais
            "trecho": c.get("texto", "")[:300],
        }
        for c in encontrados
    ]

    # Retorna a resposta final da API.
    return data