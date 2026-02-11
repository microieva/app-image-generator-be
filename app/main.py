import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import traceback
from app.core import shutdown_manager, lifespan
from .routes import (generate_image, get_generation_stream, 
                     get_generation_status, cancel_generation,
                     delete_tasks, get_tasks, get_images)


shutdown_manager.setup_signal_handlers()
app = FastAPI(lifespan=lifespan)

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