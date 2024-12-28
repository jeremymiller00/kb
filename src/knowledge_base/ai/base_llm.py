class BaseLLM:
    def set_client(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def generate_summary(self, text_snippet, summary_type='general'):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def set_logger(self, logger):
        self.logger = logger
