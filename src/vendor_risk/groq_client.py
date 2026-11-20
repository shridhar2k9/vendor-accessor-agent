from openai import OpenAI
from .config import GROQ_API_KEY, GROQ_BASE_URL, is_assessment_configured


def get_client() -> OpenAI:
    if not is_assessment_configured():
        raise RuntimeError(
            "Set GROQ_API_KEY in the environment or .env file to enable AI findings."
        )
    return OpenAI(
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
        max_retries=5,
    )