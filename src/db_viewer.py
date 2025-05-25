from fasthtml.common import *
from knowledge_base.storage.database import Database
from knowledge_base.utils.logger import logger

app, rt = fast_app()
db = Database(logger=logger)

def get_all_docs():
    # Return all documents using search_content with an empty query
    return db.search_content({}, limit=1000)  # Adjust limit as needed

def get_doc(doc_id):
    return db.get_content(doc_id)

@rt
def index():
    docs = get_all_docs()
    rows = [Tr(
        Td(A(str(doc['id']), href=doc_view.to(doc_id=doc['id']))),
        Td(doc.get('type', '')), 
        Td(doc.get('summary', '')[:80]),
        Td(doc.get('timestamp', '')),
        Td(A('Open', href=doc['url'], target='_blank'))
    ) for doc in docs]
    return Titled("Database Viewer",
        Table(
            Thead(Tr(Td('ID'), Td('Type'), Td('Summary'), Td('Timestamp'), Td('URL'))),
            Tbody(*rows)
        )
    )

@rt('/doc/{doc_id}')
def doc_view(doc_id: int):
    doc = get_doc(doc_id)
    if not doc:
        return Titled("Not Found", P(f"No document with id {doc_id}"))
    return Titled(f"Document {doc_id}",
        H2(doc.get('type', '')),
        P(B('URL: '), A(doc['url'], href=doc['url'], target='_blank')),
        P(B('Summary: '), doc.get('summary', '')),
        Pre(doc.get('content', '')),
        P(B('Keywords: '), ', '.join(doc.get('keywords', [])))
    )

serve()
