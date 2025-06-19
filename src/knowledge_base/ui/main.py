from fasthtml.common import serve, Redirect, fast_app
from ..routes.ui import app

# The main entry point for the Knowledge Base UI
if __name__ == "__main__":
    serve(app)
