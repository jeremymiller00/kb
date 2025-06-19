'''
FastAPI app for backend api
'''


import os
import time
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine
from dotenv import load_dotenv

from knowledge_base.routes import content, admin  # process: file was deprecated
from knowledge_base.utils.logger import logger

# Load environment variables
load_dotenv()


# FastAPI app
app = FastAPI(title="Knowledge Base API")


@app.middleware("http")
async def add_request_logging(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} {response.status_code} completed in {process_time:.3f}s")
    return response


# Include routers
# app.include_router(process.router) # Assuming process.router is deprecated or merged
app.include_router(content.router)
app.include_router(admin.router) # Include the new admin router


# direct to swagger ui
@app.get("/")
def read_index():
    return RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


###############################################
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)