"""
LLM + embedding provider abstraction.

Supports:
  - "watsonx"      -> IBM watsonx.ai (via ibm-watsonx-ai SDK)
  - "huggingface"  -> Hugging Face Inference API / local pipeline
  - "mock"         -> deterministic offline stub, used for local dev & CI
                       so the whole product is demoable without any
                       paid API keys.

Select provider via LLM_PROVIDER env var.
"""
from typing import List

from app.core.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------
_embedder = None


def embed_texts(texts: List[str]) -> List[List[float]]:
    if settings.LLM_PROVIDER == "mock":
        return [_mock_embedding(t) for t in texts]

    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer

        _embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _embedder.encode(texts, show_progress_bar=False).tolist()


def _mock_embedding(text: str, dim: int = 384) -> List[float]:
    """Cheap deterministic hash-based embedding so the pipeline works with
    zero external dependencies during local dev / CI smoke tests."""
    import hashlib

    seed = int(hashlib.sha256(text.encode()).hexdigest(), 16)
    return [((seed >> (i % 64)) & 0xFF) / 255.0 for i in range(dim)]


# ---------------------------------------------------------------------------
# Text generation
# ---------------------------------------------------------------------------
def generate(prompt: str, max_tokens: int = 512, temperature: float = 0.2) -> str:
    provider = settings.LLM_PROVIDER
    if provider == "watsonx":
        return _generate_watsonx(prompt, max_tokens, temperature)
    if provider == "huggingface":
        return _generate_huggingface(prompt, max_tokens, temperature)
    return _generate_mock(prompt)


def _generate_watsonx(prompt: str, max_tokens: int, temperature: float) -> str:
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference

    credentials = Credentials(url=settings.WATSONX_URL, api_key=settings.WATSONX_API_KEY)
    model = ModelInference(
        model_id=settings.WATSONX_MODEL_ID,
        credentials=credentials,
        project_id=settings.WATSONX_PROJECT_ID,
        params={"max_new_tokens": max_tokens, "temperature": temperature},
    )
    response = model.generate_text(prompt=prompt)
    return response


def _generate_huggingface(prompt: str, max_tokens: int, temperature: float) -> str:
    from huggingface_hub import InferenceClient

    client = InferenceClient(token=settings.HUGGINGFACEHUB_API_TOKEN)
    return client.text_generation(
        prompt, max_new_tokens=max_tokens, temperature=max(temperature, 0.01)
    )


def _generate_mock(prompt: str) -> str:
    """Deterministic offline response generator: extracts the CONTEXT block
    from the prompt and returns a templated, cited synthesis so the whole
    product works end-to-end without any external LLM key."""
    context_marker = "CONTEXT:"
    question_marker = "QUESTION:"
    context = ""
    question = prompt
    if context_marker in prompt and question_marker in prompt:
        context = prompt.split(context_marker, 1)[1].split(question_marker, 1)[0].strip()
        question = prompt.split(question_marker, 1)[1].strip()

    if not context:
        return f"[mock-llm] No relevant context found for: {question}"

    snippet = context[:400].replace("\n", " ")
    return (
        f"Based on the retrieved passages, here is a summary relevant to "
        f"\"{question}\": {snippet}... "
        f"(Set LLM_PROVIDER=watsonx or huggingface in .env for a real generated answer.)"
    )
