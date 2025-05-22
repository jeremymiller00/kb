"""
Manages global configuration for default LLM and embedding models.
"""

# Default values
# TODO: Consider making these more aligned with actual model identifiers if possible,
# or align with keys used in LLMFactory. For now, using placeholder names.
# For LLM, this might be a provider key like 'openai' or 'anthropic',
# and LLMFactory can then pick its internal default for that provider.
# Or, it could be a specific model name if LLMFactory is adapted.
# Let's assume for now it's a provider key for LLM, and a specific name for embedding.

_DEFAULT_LLM_PROVIDER = "openai" 
_DEFAULT_EMBEDDING_MODEL = "text-embedding-ada-002" # Example from OpenAI

def get_default_llm_provider() -> str:
    """Returns the current default LLM provider key."""
    return _DEFAULT_LLM_PROVIDER

def set_default_llm_provider(provider_key: str) -> None:
    """Sets the default LLM provider key."""
    global _DEFAULT_LLM_PROVIDER
    # Basic validation: ensure it's a non-empty string.
    # More advanced validation (e.g., against a list of supported providers) could be added.
    if not provider_key or not isinstance(provider_key, str):
        raise ValueError("LLM provider key must be a non-empty string.")
    _DEFAULT_LLM_PROVIDER = provider_key

def get_default_embedding_model() -> str:
    """Returns the current default embedding model name."""
    return _DEFAULT_EMBEDDING_MODEL

def set_default_embedding_model(model_name: str) -> None:
    """Sets the default embedding model name."""
    global _DEFAULT_EMBEDDING_MODEL
    if not model_name or not isinstance(model_name, str):
        raise ValueError("Embedding model name must be a non-empty string.")
    _DEFAULT_EMBEDDING_MODEL = model_name

# Example of how LLMFactory might use this:
# In LLMFactory.create_llm(self, provider_name=None):
#   if provider_name is None:
#       provider_name = get_default_llm_provider()
#   # ... rest of the logic ...

# Example for embedding model (perhaps in EmbeddingManager or directly):
# In some_embedding_function(model_name=None):
#   if model_name is None:
#       model_name = get_default_embedding_model()
#   # ... use model_name ...
