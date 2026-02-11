import logging
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import traceback
from app.core import shutdown_manager, lifespan
from .routes import (generate_image, get_generation_stream, 
                     get_generation_status, cancel_generation,
                     delete_tasks, get_tasks, get_images)

load_dotenv() 
shutdown_manager.setup_signal_handlers()
app = FastAPI(lifespan=lifespan)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Prevent server crash by catching all unhandled exceptions"""
    
    # Log the full error
    logger.error("="*80)
    logger.error(f"💥 UNHANDLED EXCEPTION: {type(exc).__name__}")
    logger.error(f"Request: {request.method} {request.url}")
    logger.error(f"Error: {str(exc)}")
    logger.error("Stack trace:")
    logger.error(traceback.format_exc())
    logger.error("="*80)
    
    # Return a friendly error response
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred. The server is still running."
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://172.20.10.5:3000",
        "https://client-image-generator.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"📨 Incoming request: {request.method} {request.url}")
    
    if request.method == "POST" and request.url.path == "/generate":
        try:
            body = await request.json()
            logger.info(f"📦 /generate request body: {body}")
        except:
            logger.info("📦 /generate request (could not parse body)")
    
    try:
        response = await call_next(request)
        logger.info(f"📤 Response: {response.status_code} for {request.method} {request.url.path}")
        return response
    except Exception as e:
        logger.error(f"💥 Unhandled error in {request.method} {request.url.path}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise

app.include_router(generate_image)
app.include_router(get_generation_stream)
app.include_router(get_generation_status)
app.include_router(cancel_generation)
app.include_router(delete_tasks)
app.include_router(get_tasks)
app.include_router(get_images)  

@app.get("/")
async def root():
    return {"message": "App server running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)