import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
_configured_model = (
    os.getenv("GROQ_MODEL_ID", "").strip()
    or os.getenv("GROQ_MODEL", "").strip()
)
GROQ_MODEL_IS_PLACEHOLDER = _configured_model.lower().startswith("replace_with_")
GROQ_MODEL_ID = _configured_model or "openai/gpt-oss-120b"
GROQ_MODEL = GROQ_MODEL_ID
GROQ_BASE_URL = (
    os.getenv("GROQ_BASE_URL", "").strip()
    or "https://api.groq.com/openai/v1"
)


def is_assessment_configured() -> bool:
    return bool(GROQ_API_KEY and GROQ_MODEL and not GROQ_MODEL_IS_PLACEHOLDER)