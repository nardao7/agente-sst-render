import os

# -----------------------------
# PROVEDOR PRINCIPAL
# -----------------------------
# Pode ser: gemini ou openai
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").strip().lower()

# -----------------------------
# GEMINI
# -----------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
GEMINI_ENABLED = bool(GEMINI_API_KEY)

# -----------------------------
# OPENAI
# -----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
OPENAI_ENABLED = bool(OPENAI_API_KEY)