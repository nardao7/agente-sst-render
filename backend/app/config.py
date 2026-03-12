import os

# Chave da OpenAI lida a partir das variáveis de ambiente do Render
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# Modelo usado pela OpenAI
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()

# Flag para sabermos se a OpenAI está realmente configurada
OPENAI_ENABLED = bool(OPENAI_API_KEY)