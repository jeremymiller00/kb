import pytest
from unittest.mock import patch, MagicMock

# Assuming your project structure allows this import path
from src.knowledge_base.ai.llm_factory import LLMFactory
from src.knowledge_base.ai.openai_llm import OpenAILLM 
# If AnthropicLLM is implemented and used by default or in tests:
# from src.knowledge_base.ai.anthropic_llm import AnthropicLLM 
from src.knowledge_base.config_manager import get_default_llm_provider, set_default_llm_provider, _DEFAULT_LLM_PROVIDER

# Mock the actual LLM client classes if their __init__ does more than just assign attributes
# For this test, we are primarily testing the factory's logic to select and instantiate.
# So, we might not need to mock the classes themselves unless their instantiation is complex/problematic for tests.

@pytest.fixture
def factory():
    """Returns an LLMFactory instance."""
    return LLMFactory()

@pytest.fixture(autouse=True)
def reset_config_manager_defaults():
    """Fixture to reset config_manager default values after each test."""
    original_llm_provider = get_default_llm_provider()
    yield
    set_default_llm_provider(original_llm_provider) # Reset to whatever it was before the test


def test_create_llm_specified_provider_openai(factory):
    """Test creating an LLM client with 'openai' provider specified."""
    # Mock the OpenAILLM class to ensure we can check its instantiation
    # For this example, we assume OpenAILLM is a known class.
    # If its __init__ has side effects (e.g., API calls), you might want to mock it more deeply.
    llm_instance = factory.create_llm(provider_name="openai")
    assert isinstance(llm_instance, OpenAILLM)

# Example for Anthropic, if it were implemented and part of the factory's known providers
# def test_create_llm_specified_provider_anthropic(factory):
#     """Test creating an LLM client with 'anthropic' provider specified."""
#     # This assumes AnthropicLLM is a class and 'anthropic' is a key in factory.providers
#     # You would need to import AnthropicLLM similar to OpenAILLM
#     # For now, let's assume it's not fully implemented or we don't have the class
#     if "anthropic" in factory.providers:
#          llm_instance = factory.create_llm(provider_name="anthropic")
#          assert isinstance(llm_instance, AnthropicLLM) # Replace AnthropicLLM with the actual class
#     else:
#         pytest.skip("Anthropic provider not configured in LLMFactory for this test")


@patch('src.knowledge_base.ai.llm_factory.get_default_llm_provider')
def test_create_llm_uses_default_provider(mock_get_default, factory):
    """Test that create_llm uses the default provider when none is specified."""
    # Set a known default provider for the duration of this test
    default_provider_for_test = "openai" # Assuming 'openai' is a valid key
    mock_get_default.return_value = default_provider_for_test
    
    # We need to ensure that the factory correctly uses this default to instantiate OpenAILLM
    # The factory's internal __import__ and getattr will be used.
    # If OpenAILLM is the class for 'openai', this should work.
    llm_instance = factory.create_llm() # No provider_name specified
    assert isinstance(llm_instance, OpenAILLM)
    mock_get_default.assert_called_once()

@patch('src.knowledge_base.ai.llm_factory.get_default_llm_provider')
def test_create_llm_default_provider_dynamic(mock_get_default, factory):
    """Test that create_llm correctly uses a dynamically set default provider."""
    # Scenario: Default is 'openai', then changed to 'anthropic' (if supported)
    
    # Initial default is 'openai'
    mock_get_default.return_value = "openai"
    llm_instance_openai = factory.create_llm()
    assert isinstance(llm_instance_openai, OpenAILLM)
    
    # Change default provider (hypothetically, if 'anthropic' was supported and different)
    # This part of the test depends on 'anthropic' being a recognized provider in the factory
    if "anthropic" in factory.providers:
        # from src.knowledge_base.ai.anthropic_llm import AnthropicLLM # Make sure this is imported
        mock_get_default.return_value = "anthropic"
        # llm_instance_anthropic = factory.create_llm()
        # assert isinstance(llm_instance_anthropic, AnthropicLLM) # Replace with actual class
    else:
        # If 'anthropic' is not a distinct, implemented provider, we can't test dynamic switching to it this way.
        # We can, however, test that the factory *tries* to use the new default.
        # For this, we'd need to mock the import mechanism if the provider is unknown.
        # But the factory is designed to raise ValueError for unknown providers *after* getting the default.
        pass # Adjust if 'anthropic' or another provider is fully implemented for testing.


def test_create_llm_unknown_provider(factory):
    """Test creating an LLM client with an unknown provider raises ValueError."""
    unknown_provider = "unknown_magic_llm"
    with pytest.raises(ValueError) as excinfo:
        factory.create_llm(provider_name=unknown_provider)
    assert f"Provider '{unknown_provider}' is not supported" in str(excinfo.value)
    assert "Supported providers are:" in str(excinfo.value)

@patch('src.knowledge_base.ai.llm_factory.get_default_llm_provider')
def test_create_llm_unknown_default_provider(mock_get_default, factory):
    """Test factory behavior if default provider from config_manager is unknown."""
    unknown_default = "non_existent_default_provider"
    mock_get_default.return_value = unknown_default
    
    with pytest.raises(ValueError) as excinfo:
        factory.create_llm() # No provider specified, should use default
    assert f"Provider '{unknown_default}' is not supported" in str(excinfo.value)
    mock_get_default.assert_called_once()

# To test the dynamic import part of the factory more deeply,
# you might need to mock `__import__` or `getattr`, but that can get complex.
# The current tests focus on the factory's logic given its known providers.

# Example: Test successful import and instantiation for all known providers
# This assumes that the corresponding LLM client classes (OpenAILLM, AnthropicLLM, etc.)
# can be instantiated without side effects or with their side effects mocked.
def test_create_llm_for_all_known_providers(factory):
    """Test creating LLM clients for all providers listed in the factory."""
    for provider_name in factory.providers.keys():
        # Dynamically get the expected class type based on provider_name
        # This requires the class itself to be importable in the test file.
        expected_class_str = factory.providers[provider_name]
        
        # Attempt to import the class. This is a bit meta for a test but shows capability.
        # This assumes 'src.knowledge_base.ai.openai_llm' and similar for other modules.
        module_name_str = factory.modules[provider_name]
        try:
            module = __import__(f"src.knowledge_base.ai.{module_name_str}", fromlist=[expected_class_str])
            ExpectedClass = getattr(module, expected_class_str)
        except ImportError:
            pytest.fail(f"Could not import class {expected_class_str} from module {module_name_str} for provider {provider_name}")
        
        llm_instance = factory.create_llm(provider_name)
        assert isinstance(llm_instance, ExpectedClass), \
            f"Failed for provider '{provider_name}'. Expected instance of {expected_class_str}."

# Note: If AnthropicLLM or other LLMs are not yet implemented,
# the 'anthropic' related tests will need to be adjusted or skipped.
# For instance, if 'anthropic' is in providers but AnthropicLLM class is not created/imported,
# test_create_llm_for_all_known_providers would fail for 'anthropic'.
# Ensure that your factory.providers and factory.modules only list fully implemented and testable providers.

# If a provider is listed but its module or class cannot be imported by the factory at runtime,
# the factory's try-except block for ImportError/AttributeError should be tested.
# This is implicitly covered if a provider is in `factory.providers` but its module `factory.modules[provider]`
# or class `factory.providers[provider]` (the class name string) is incorrect.

@patch('src.knowledge_base.ai.llm_factory.__import__')
def test_create_llm_import_error_handling(mock_import, factory):
    """Test that create_llm handles ImportError during dynamic module loading."""
    mock_import.side_effect = ImportError("Test import error")
    
    # Test with a provider that would trigger the import attempt
    provider_to_test = "openai" # Assuming this is a configured provider
    if provider_to_test not in factory.providers:
        pytest.skip(f"Provider '{provider_to_test}' not in factory.providers, skipping ImportError test.")

    with pytest.raises(ImportError, match="Test import error"):
        factory.create_llm(provider_name=provider_to_test)
    mock_import.assert_called_once()


@patch('src.knowledge_base.ai.llm_factory.__import__')
def test_create_llm_attribute_error_handling(mock_import, factory):
    """Test that create_llm handles AttributeError if class not found in module."""
    # Mock the imported module
    mock_module = MagicMock()
    # Make getattr raise AttributeError when trying to get the class
    mock_module.side_effect = AttributeError("Test attribute error: class not found") # This is not quite right for mocking getattr
    
    # Correct way to mock module and then have getattr fail on it:
    # 1. __import__ returns a mock module.
    # 2. getattr(mock_module, "ClassName") raises AttributeError.
    
    mock_imported_module = MagicMock()
    mock_import.return_value = mock_imported_module
    
    # Configure the mock_imported_module so that accessing the expected class attribute raises AttributeError
    provider_to_test = "openai"
    if provider_to_test not in factory.providers:
        pytest.skip(f"Provider '{provider_to_test}' not in factory.providers, skipping AttributeError test.")
        
    expected_class_name = factory.providers[provider_to_test]
    
    # Make getattr(mock_imported_module, expected_class_name) raise AttributeError
    # This is done by setting a side_effect on the mock_imported_module if it were directly callable,
    # or by configuring its __getattr__ if it's a more complex object.
    # For a simple MagicMock, we can make it so that trying to get any attribute that's not explicitly set
    # could raise an error, or specifically for the expected class name.
    
    # A simpler way for specific attribute:
    # Set all attributes, then delete the one we want to cause an AttributeError for.
    # However, MagicMock creates attributes on demand.
    # So, we make getattr on this mock object raise the error.
    
    def mock_getattr(name):
        if name == expected_class_name:
            raise AttributeError(f"Test: Class {name} not found")
        return MagicMock() # Default behavior for other attributes

    mock_imported_module.__getattr__ = mock_getattr
            
    with pytest.raises(AttributeError, match=f"Test: Class {expected_class_name} not found"):
        factory.create_llm(provider_name=provider_to_test)
    
    mock_import.assert_called_once_with(
        f"knowledge_base.ai.{factory.modules[provider_to_test].lower()}",
        fromlist=[expected_class_name]
    )
