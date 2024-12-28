# from src.knowledge_base.utils.config import configure_logging

# logger = configure_logging()


class LLMFactory:
    def __init__(self):
        self.providers = {
            'openai': 'OpenAILLM',
            'anthropic': 'AnthropicLLM'
        }
        self.modules = {
            'openai': 'openai_llm',
            'anthropic': 'anthropic_llm'
        }

    def create_llm(self, provider_name):     
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' is not supported.")
        
        provider_class_name = self.providers[provider_name]
        
        try:
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