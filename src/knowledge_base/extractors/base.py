from abc import ABC, abstractmethod


class ContentExtractor(ABC):
    def __init__(self):
        self.logger = None

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        pass
    
    @abstractmethod
    def extract(self, url: str, work=None) -> str:
        pass
    
    @staticmethod
    def normalize_url(url: str) -> str:
        if not url.startswith(('http://', 'https://')):
            return f'https://{url}'
        return url

    def set_logger(self, logger):
        self.logger = logger
