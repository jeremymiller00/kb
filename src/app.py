'''
FastAPI app for backend api
'''


import os
import time
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from dotenv import load_dotenv

from knowledge_base.routes import content, admin, suggestions
from knowledge_base.ai.openai_llm import OpenAILLM
from knowledge_base.utils.logger import logger

# Load environment variables
load_dotenv()


# FastAPI app
app = FastAPI(title="Knowledge Base API")

# Add CORS middleware to allow UI calls from port   5001
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5001", "http://0.0.0.0:5001", "http://127.0.0.1:5001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_logging(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} {response.status_code} completed in {process_time:.3f}s")
    return response


# Include routers
app.include_router(content.router)
app.include_router(admin.router)
app.include_router(suggestions.router)

# # Real OpenAI suggestions router with enhanced fallback
# from fastapi import APIRouter
# import random
# import asyncio
# from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

# suggestions_router = APIRouter(prefix="/api", tags=["suggestions-openai"])

# Enhanced suggestion templates by type
SUGGESTION_TEMPLATES = {
    "question": [
        "What are the key technical challenges for implementing this in healthcare?",
        "How does this approach compare to existing solutions in the market?",
        "What are the potential risks and mitigation strategies?",
        "How would you measure the success of this implementation?",
        "What regulatory considerations need to be addressed?",
        "How scalable is this solution across different healthcare settings?",
        "What data privacy concerns need to be addressed?",
        "How would this integrate with existing healthcare systems?"
    ],
    "strategy": [
        "How could this be prioritized in a healthcare AI product roadmap?",
        "What would be the business case for investing in this approach?",
        "How could this differentiate our product in the healthcare AI market?",
        "What partnerships would be needed to implement this effectively?",
        "How would this impact time-to-market for new features?",
        "What would be the ideal go-to-market strategy for this solution?",
        "How could this solution create network effects in healthcare?",
        "What would be the total addressable market for this approach?"
    ],
    "application": [
        "Which healthcare workflows would benefit most from this solution?",
        "How could this be applied to improve patient outcomes?",
        "What clinical use cases would see the highest ROI?",
        "How could this solution reduce healthcare costs?",
        "What types of healthcare providers would adopt this first?",
        "How could this improve clinical decision-making?",
        "What operational efficiencies could this create?",
        "How could this enhance the patient experience?"
    ],
    "implementation": [
        "What would be the minimum viable product for this solution?",
        "What technical infrastructure would be required?",
        "How would you approach data integration challenges?",
        "What would be the implementation timeline and milestones?",
        "What expertise and team composition would be needed?",
        "How would you handle change management with clinical staff?",
        "What would be the key performance indicators to track?",
        "How would you ensure HIPAA compliance during implementation?"
    ],
    "topic": [
        "How does this relate to current trends in digital health?",
        "What are the ethical implications of this approach?",
        "How could this contribute to healthcare equity initiatives?",
        "What role does AI explainability play in this solution?",
        "How does this align with value-based care models?",
        "What are the implications for healthcare workforce transformation?",
        "How could this support preventive care strategies?",
        "What are the long-term implications for healthcare delivery?"
    ]
}

# def generate_fallback_suggestions(article_id: str, count: int = 5, force_fresh: bool = True):
#     """Generate enhanced fallback suggestions with realistic healthcare AI PM content."""
#     print(f"DEBUG: Using fallback suggestions for article {article_id}")
#     count = min(max(count, 1), 20)
#     suggestions = []
#     suggestion_types = list(SUGGESTION_TEMPLATES.keys())
    
#     for i in range(count):
#         suggestion_type = suggestion_types[i % len(suggestion_types)]
#         template = random.choice(SUGGESTION_TEMPLATES[suggestion_type])
#         suggestions.append({
#             "type": suggestion_type,
#             "content": template
#         })
    
#     return {
#         "suggestions": suggestions,
#         "context": {
#             "fallback": True, 
#             "reason": "OpenAI integration failed - using enhanced templates",
#             "article_id": article_id,
#             "suggestion_count": count,
#             "fresh_generation": force_fresh
#         },
#         "success": True
#     }

# @app.get("/api/suggestions/{article_id}")
# def generate_openai_suggestions(article_content: str, count: int = 5):
#     """Generate AI suggestions using the existing OpenAI LLM implementation."""
#     try:
        
#         # Initialize OpenAI client
#         llm = OpenAILLM()
#         llm.set_logger(logger)  # Set the logger
        
#         # Create healthcare AI PM persona prompt
#         system_prompt = """You are generating suggestions for an AI Product Manager at a healthcare analytics company.
#         Focus on practical AI solutions, product strategy, implementation challenges, regulatory considerations, and business impact.
        
#         Generate exactly {count} suggestions in the following format, covering different types:
#         - Questions: Technical challenges, risks, compliance, scalability
#         - Strategy: Business case, roadmap, market differentiation, partnerships  
#         - Application: Clinical workflows, patient outcomes, cost reduction
#         - Implementation: MVP, infrastructure, timelines, change management
#         - Topics: Digital health trends, ethics, healthcare transformation
        
#         Return a JSON array with objects containing "type" and "content" fields.
#         Types should be: question, strategy, application, implementation, or topic.""".format(count=count)
        
#         user_prompt = f"Based on this healthcare/AI content, generate {count} relevant suggestions:\n\n{article_content[:2000]}"
        
#         # Generate suggestions with timeout
#         response = llm.gen_gpt_chat_completion(
#             system_prompt=system_prompt,
#             user_prompt=user_prompt,
#             temperature=0.8,
#             max_tokens=800
#         )
        
#         # Parse response
#         content = response.choices[0].message.content.strip()
        
#         # Try to parse as JSON, fallback to text parsing
#         import json
#         try:
#             suggestions_data = json.loads(content)
#             if isinstance(suggestions_data, list):
#                 return suggestions_data
#         except:
#             pass
        
#         # Fallback: parse text response
#         suggestions = []
#         lines = content.split('\n')
#         for line in lines[:count]:
#             if line.strip() and not line.startswith('#'):
#                 suggestions.append({
#                     "type": "question",  # Default type
#                     "content": line.strip()
#                 })
        
#         return suggestions[:count]
        
#     except Exception as e:
#         logger.error(f"OpenAI suggestion generation failed: {e}")
#         raise

# async def get_ai_suggestions_direct(article_id: str, count: int = 5, force_fresh: bool = True):
#     """Generate AI suggestions using OpenAI directly - bypassing router."""
#     # for debugging purposes, currently diabled
#     print(f"DEBUG: Direct OpenAI suggestions for article {article_id}")
    
#     try:
#         # Get article content directly from the content manager instead of self-request
#         try:
#             from knowledge_base.core.content_manager import ContentManager
#             import logging
#             content_logger = logging.getLogger("content_manager")
#             content_manager = ContentManager(content_logger, os.getenv('DB_CONN_STRING'))
            
#             article_data = content_manager.get_document_by_id(int(article_id))
#             if article_data:
#                 article_content = (article_data.get('content', '') + '\n' + 
#                                  article_data.get('summary', ''))[:2000]
#             else:
#                 article_content = f"Article {article_id} - content not found in database"
#         except Exception as e:
#             print(f"DEBUG: Content fetch error: {e}")
#             article_content = f"Article {article_id} - fallback content for testing OpenAI integration"
        
#         # Try direct OpenAI call
#         try:
#             import openai
#             client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
            
#             system_prompt = """You are an AI Product Manager at a healthcare analytics company. 
#             Generate exactly 3-5 practical suggestions based on the content provided.
            
#             Format your response as a JSON array with objects containing "type" and "content" fields.
#             Types should be: question, strategy, application, implementation, or topic.
            
#             Focus on: healthcare AI applications, product strategy, implementation challenges, regulatory considerations."""
            
#             user_prompt = f"Based on this content, generate {count} relevant suggestions for a healthcare AI PM:\n\n{article_content}"
            
#             response = client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=[
#                     {"role": "system", "content": system_prompt},
#                     {"role": "user", "content": user_prompt}
#                 ],
#                 temperature=0.8,
#                 max_tokens=600,
#                 timeout=10
#             )
            
#             content = response.choices[0].message.content.strip()
#             print(f"DEBUG: OpenAI response: {content}")
            
#             # Clean up JSON - remove markdown code blocks
#             if content.startswith('```json'):
#                 content = content[7:]  # Remove ```json
#             if content.startswith('```'):
#                 content = content[3:]   # Remove ```
#             if content.endswith('```'):
#                 content = content[:-3]  # Remove ending ```
#             content = content.strip()
            
#             # Try to parse as JSON
#             import json
#             try:
#                 suggestions = json.loads(content)
#                 if isinstance(suggestions, list) and len(suggestions) > 0:
#                     print(f"DEBUG: Successfully parsed {len(suggestions)} suggestions from JSON")
#                     return {
#                         "suggestions": suggestions,
#                         "context": {
#                             "fallback": False,
#                             "ai_generated": True,
#                             "model": "gpt-4o-mini",
#                             "article_id": article_id,
#                             "suggestion_count": len(suggestions)
#                         },
#                         "success": True
#                     }
#             except json.JSONDecodeError as e:
#                 print(f"DEBUG: JSON parse error: {e}")
#                 pass
            
#             # Fallback: parse as text
#             lines = [line.strip() for line in content.split('\n') if line.strip()]
#             suggestions = []
#             for i, line in enumerate(lines[:count]):
#                 suggestions.append({
#                     "type": ["question", "strategy", "application", "implementation", "topic"][i % 5],
#                     "content": line
#                 })
            
#             print(f"DEBUG: Using text parsing, got {len(suggestions)} suggestions")
#             return {
#                 "suggestions": suggestions,
#                 "context": {
#                     "fallback": False,
#                     "ai_generated": True,
#                     "model": "gpt-4o-mini",
#                     "article_id": article_id,
#                     "suggestion_count": len(suggestions),
#                     "parsed_as": "text"
#                 },
#                 "success": True
#             }
            
#         except Exception as e:
#             print(f"DEBUG: OpenAI error: {e}")
#             return generate_fallback_suggestions(article_id, count, force_fresh)
            
#     except Exception as e:
#         print(f"DEBUG: General error: {e}")
#         return generate_fallback_suggestions(article_id, count, force_fresh)

# # app.include_router(suggestions_router)  # Disabled - using direct endpoint instead
# logger.info("Direct OpenAI suggestions endpoint loaded")

# # List all registered routes for debugging
# print("DEBUG: Registered routes:")
# for route in app.routes:
#     if hasattr(route, 'path') and 'suggestions' in route.path:
#         print(f"  {route.methods} {route.path} -> {route.endpoint}")
# print("DEBUG: Route registration complete")


# # Test endpoint for debugging
# @app.get("/test-suggestions")
# async def test_suggestions():
#     print("DEBUG: test-suggestions endpoint called")
#     return {"status": "test endpoint working", "debug": True}

# # Test endpoint for OpenAI connectivity
# @app.get("/test-openai")
# async def test_openai():
#     try:
#         import openai
#         import os
#         client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role": "user", "content": "Say 'OpenAI is working!'"}],
#             max_tokens=20,
#             timeout=10
#         )
#         return {"status": "success", "response": response.choices[0].message.content}
#     except Exception as e:
#         return {"status": "error", "error": str(e)}

# direct to swagger ui
@app.get("/")
def read_index():
    return RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


###############################################
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)