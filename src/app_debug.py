"""
Debug FastAPI app - step by step
"""

import os
import time
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from dotenv import load_dotenv

print("1. Basic imports completed")

# Load environment variables
load_dotenv()
print("2. Environment variables loaded")

# FastAPI app
app = FastAPI(title="Knowledge Base API")
print("3. FastAPI app created")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5001", "http://0.0.0.0:5001", "http://127.0.0.1:5001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("4. CORS middleware added")

@app.middleware("http")
async def add_request_logging(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"{request.method} {request.url.path} {response.status_code} completed in {process_time:.3f}s")
    return response

print("5. Request logging middleware added")

try:
    from knowledge_base.routes import content
    print("6. Content router imported")
    app.include_router(content.router)
    print("7. Content router included")
except Exception as e:
    print(f"Error with content router: {e}")

try:
    from knowledge_base.routes import admin
    print("8. Admin router imported")
    app.include_router(admin.router)
    print("9. Admin router included")
except Exception as e:
    print(f"Error with admin router: {e}")

try:
    from knowledge_base.utils.logger import logger
    print("10. Logger imported")
except Exception as e:
    print(f"Error with logger: {e}")

# Root route
@app.get("/")
def read_index():
    return RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

print("11. Root route added")

if __name__ == "__main__":
    print("12. Starting uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)