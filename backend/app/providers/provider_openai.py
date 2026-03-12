import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_ENABLED
from app.providers.provider_base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """
    Provedor OpenAI.
    Atua como secundário/fallback de LLM.
    """

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_ENABLED else None

    def is_available(self) -> bool:
        return OPENAI_ENABLED and self.client is not None

    def generate_structured_response(self, pergunta: str, contexto: str, system_prompt: str) -> dict:
        if not self.is_available():
            raise RuntimeError("OpenAI não está disponível.")

        response = self.client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"""
Pergunta do usuário:
{pergunta}

Fontes recuperadas:
{contexto}

Retorne apenas JSON válido.
""",
                },
            ],
        )

        text = response.output_text.strip()
        return json.loads(text)