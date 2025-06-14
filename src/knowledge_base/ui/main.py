from fasthtml.common import serve, Redirect, fast_app
from src.knowledge_base.routes.ui import app

# The main entry point for the Knowledge Base UI
if __name__ == "__main__":
    serve(app)
