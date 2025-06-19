# from src.knowledge_base.utils.config import configure_logging

# logger = configure_logging()

from ..config_manager import get_default_llm_provider

class LLMFactory:
    def __init__(self):
        self.providers = {
            'openai': 'OpenAILLM',
            'anthropic': 'AnthropicLLM'
            # Add other providers here as they are implemented
        }
        self.modules = {
            'openai': 'openai_llm',
            'anthropic': 'anthropic_llm'
            # Corresponding module names
        }

    def create_llm(self, provider_name: str = None):     
        if provider_name is None:
            provider_name = get_default_llm_provider()
            # Potentially log that we're using the default provider
            # print(f"LLMFactory: No provider specified, using default: {provider_name}") # For debugging

        if provider_name not in self.providers:
            # Consider logging this error before raising
            raise ValueError(f"Provider '{provider_name}' is not supported. Supported providers are: {list(self.providers.keys())}")
        
        provider_class_name = self.providers[provider_name]
        
        try:
            # Try to import using relative import first, then absolute import with src prefix
            try:
                from . import openai_llm, remote_llm
                module_name = self.modules[provider_name].lower()
                if module_name == 'openai_llm':
                    module = openai_llm
                elif module_name == 'anthropic_llm' or module_name == 'remote_llm':
                    module = remote_llm
                else:
                    raise ImportError(f"Unknown module: {module_name}")
            except ImportError:
                # Fallback to absolute import
                module = __import__(
                    f"src.knowledge_base.ai.{self.modules[provider_name].lower()}", 
                    fromlist=[provider_class_name])
            
            provider_class = getattr(module, provider_class_name)
            
            instance = provider_class()
            return instance
            
        except ImportError as e:
            print(f"Failed to import module for provider {provider_name}: {str(e)}")
            raise
        except AttributeError as e:
            print(f"Failed to get provider class {provider_class_name}: {str(e)}")
            raise
        except Exception as e:
            print(f"Unexpected error creating LLM instance: {str(e)}")
            raise