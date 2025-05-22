"""
API Routes for Adminstrative tasks, including managing default model configurations.
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict

from knowledge_base.config_manager import (
    get_default_llm_provider,
    set_default_llm_provider,
    get_default_embedding_model,
    set_default_embedding_model
)
from knowledge_base.core.models import ModelConfig # Assuming ModelConfig is for { "model_name": "..." }

router = APIRouter(prefix="/admin", tags=["Admin"])

# LLM Configuration Endpoints
@router.get("/default-llm", response_model=ModelConfig)
async def get_current_default_llm():
    """Retrieves the current default LLM provider key."""
    return ModelConfig(model_name=get_default_llm_provider())

@router.post("/default-llm", response_model=ModelConfig)
async def update_default_llm(config: ModelConfig):
    """Updates the default LLM provider key."""
    try:
        set_default_llm_provider(config.model_name)
        return ModelConfig(model_name=get_default_llm_provider())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e: # Catch any other unexpected errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

# Embedding Model Configuration Endpoints
@router.get("/default-embedding-model", response_model=ModelConfig)
async def get_current_default_embedding_model():
    """Retrieves the current default embedding model name."""
    return ModelConfig(model_name=get_default_embedding_model())

@router.post("/default-embedding-model", response_model=ModelConfig)
async def update_default_embedding_model(config: ModelConfig):
    """Updates the default embedding model name."""
    try:
        set_default_embedding_model(config.model_name)
        return ModelConfig(model_name=get_default_embedding_model())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

# Simple status endpoint for the admin router
@router.get("/status", response_model=Dict[str, str])
async def get_admin_status():
    """Returns the status of the Admin router."""
    return {"status": "Admin router is active"}
