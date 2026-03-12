import json
from google import genai

from app.config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_ENABLED
from app.providers.provider_base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """
    Provedor Gemini.
    Usa a API do Google como principal nesta arquitetura.
    """

    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_ENABLED else None

    def is_available(self) -> bool:
        return GEMINI_ENABLED and self.client is not None

    def generate_structured_response(self, pergunta: str, contexto: str, system_prompt: str) -> dict:
        if not self.is_available():
            raise RuntimeError("Gemini não está disponível.")

        prompt = f"""
{system_prompt}

Pergunta do usuário:
{pergunta}

Fontes recuperadas:
{contexto}

Retorne apenas JSON válido.
"""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        text = response.text.strip()
        return json.loads(text)