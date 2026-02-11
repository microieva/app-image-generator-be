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

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled exception: {exc}")
    traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers={
            "Access-Control-Allow-Origin": "https://client-image-generator.vercel.app",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

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