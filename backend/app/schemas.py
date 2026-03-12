from pydantic import BaseModel
from typing import List, Optional


class AskRequest(BaseModel):
    pergunta: str


class SourceItem(BaseModel):
    documento: str
    item: Optional[str] = None
    titulo: Optional[str] = None
    referencia: Optional[str] = None
    trecho: Optional[str] = None
    tipo_fonte: Optional[str] = None


class AskResponse(BaseModel):
    resposta_objetiva: str
    base_normativa_legal: str
    explicacao_pratica: str
    limite_tecnico: str
    trecho_normativo_exato: str
    fontes: List[SourceItem]
    nivel_confianca: str
    modo_resposta: str