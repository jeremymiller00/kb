import pytest
from src.knowledge_base.config_manager import (
    get_default_llm_provider,
    set_default_llm_provider,
    get_default_embedding_model,
    set_default_embedding_model,
    _DEFAULT_LLM_PROVIDER,  # Import initial default for resetting
    _DEFAULT_EMBEDDING_MODEL # Import initial default for resetting
)

@pytest.fixture(autouse=True)
def reset_defaults():
    """Fixture to reset default values after each test."""
    original_llm = get_default_llm_provider()
    original_embedding = get_default_embedding_model()
    yield
    # Reset to initial defaults loaded from the module, not necessarily the ones at the start of the test run
    # This assumes the module's initial state is what we want to revert to.
    # A more robust way might be to store the defaults at the beginning of the test session.
    set_default_llm_provider(_DEFAULT_LLM_PROVIDER)
    set_default_embedding_model(_DEFAULT_EMBEDDING_MODEL)


def test_get_default_llm_provider():
    """Test retrieving the default LLM provider."""
    assert get_default_llm_provider() == _DEFAULT_LLM_PROVIDER

def test_set_default_llm_provider():
    """Test setting and retrieving the default LLM provider."""
    new_provider = "anthropic"
    set_default_llm_provider(new_provider)
    assert get_default_llm_provider() == new_provider

    new_provider_2 = "openai_test"
    set_default_llm_provider(new_provider_2)
    assert get_default_llm_provider() == new_provider_2

def test_set_default_llm_provider_invalid():
    """Test setting default LLM provider with invalid values."""
    with pytest.raises(ValueError, match="LLM provider key must be a non-empty string."):
        set_default_llm_provider("")
    with pytest.raises(ValueError, match="LLM provider key must be a non-empty string."):
        set_default_llm_provider(None)
    with pytest.raises(ValueError, match="LLM provider key must be a non-empty string."):
        set_default_llm_provider(123) # type: ignore

def test_get_default_embedding_model():
    """Test retrieving the default embedding model."""
    assert get_default_embedding_model() == _DEFAULT_EMBEDDING_MODEL

def test_set_default_embedding_model():
    """Test setting and retrieving the default embedding model."""
    new_model = "custom-embedding-model-v1"
    set_default_embedding_model(new_model)
    assert get_default_embedding_model() == new_model

    new_model_2 = "another-model-v2"
    set_default_embedding_model(new_model_2)
    assert get_default_embedding_model() == new_model_2

def test_set_default_embedding_model_invalid():
    """Test setting default embedding model with invalid values."""
    with pytest.raises(ValueError, match="Embedding model name must be a non-empty string."):
        set_default_embedding_model("")
    with pytest.raises(ValueError, match="Embedding model name must be a non-empty string."):
        set_default_embedding_model(None)
    with pytest.raises(ValueError, match="Embedding model name must be a non-empty string."):
        set_default_embedding_model(456) # type: ignore
