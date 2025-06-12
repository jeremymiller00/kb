from fasthtml.common import serve, Redirect
from src.knowledge_base.routes.ui import router as app

rt = app.route


@rt
def index():
    return Redirect('/ui')


serve()
