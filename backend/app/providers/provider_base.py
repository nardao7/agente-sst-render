from abc import ABC, abstractmethod
from typing import List, Dict


class BaseLLMProvider(ABC):
    """
    Classe base para todos os provedores de IA.
    Todo provedor deve implementar:
    - is_available()
    - generate_structured_response()
    """

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def generate_structured_response(self, pergunta: str, contexto: str, system_prompt: str) -> dict:
        pass