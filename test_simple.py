from fasthtml.common import *

app, rt = fast_app()

@rt
def index():
    return Div(
        H1("Hello World!"),
        style="background: #101510; color: #39ff14; font-family: monospace; padding: 2rem;"
    )

if __name__ == "__main__":
    serve()