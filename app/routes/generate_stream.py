import datetime
import json
import os
import sys
import aiohttp
from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.core.config import settings
from app.core.database import get_db
from app.events.db_events import update_task_in_db, save_image_to_db
from app.schemas.schemas import GenerationResult
load_dotenv() 
logger = logging.getLogger(__name__)
router = APIRouter()

_sse_buffers = {}

def handle_db_event(task_id: str, chunk: bytes, db: Session): 
    try:
        if task_id not in _sse_buffers:
            _sse_buffers[task_id] = b""

        _sse_buffers[task_id] += chunk
        
        buffer = _sse_buffers[task_id]
        complete_messages = []
        
        while b"\n\n" in buffer:
            message_bytes, buffer = buffer.split(b"\n\n", 1)
            
            try:
                message_str = message_bytes.decode('utf-8').strip()
                complete_messages.append(message_str)
            except UnicodeDecodeError:
                logger.error(f"❌ Failed to decode message for task {task_id}")
                continue
        
        _sse_buffers[task_id] = buffer
        
        for message_str in complete_messages:
            process_complete_message(task_id, message_str, db)
            
        if len(buffer) > 10000:
            logger.warning(f"⚠️ Large buffer for task {task_id}: {len(buffer)} bytes")
            
    except Exception as e:
        logger.error(f"Error handling DB event for task {task_id}: {e}")
        import traceback
        traceback.print_exc()
        if task_id in _sse_buffers:
            del _sse_buffers[task_id]

def process_complete_message(task_id: str, message_str: str, db: Session):
    try:    
        if message_str.startswith("data: "):
            data_str = message_str[6:].strip() 
            
            try:
                data = json.loads(data_str)
                
                if "status" in data:
                    status = data["status"]
                    progress = int(round(float(data.get("progress", 100))))
                    update_task_in_db(task_id, {"status": status, "progress": progress}, db)
                    
                    if status == "completed":    
                        if "result" in data:
                            result = GenerationResult(
                                task_id=task_id,
                                image_data=data["result"]["image"],
                                prompt=data["result"]["prompt"],
                                model_used=data["result"]["model_used"],
                                total_inference_time=data["result"]["total_inference_time"],
                                completed_at=datetime.datetime.now().isoformat()
                            )
                            save_image_to_db(result, db)
                            update_task_in_db(task_id, {"status": data['status'], "progress": 100}, db)
                    
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON decode error in complete message: {e}")
                
            
    except Exception as e:
        logger.error(f"❌ Error processing complete message for {task_id}: {e}")
        import traceback
        traceback.print_exc()

@router.get("/generate-stream/{task_id}")
async def generate_stream(task_id: str, db: Session = Depends(get_db)):
    async def proxy():
        space_url = f"{settings.HF_SPACE_URL}/generate-stream/{task_id}"    
        headers = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Authorization": f"Bearer {settings.HF_TOKEN}"
        }
        
        try:
            timeout = aiohttp.ClientTimeout(
                total=3600, 
                connect=30,     
                sock_read=300, 
                sock_connect=30  
            )
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(space_url, headers=headers) as response:
                    if response.status != 200:
                        error = await response.text()
                        yield f"data: {json.dumps({'error': error[:200]})}\n\n"
                        return
                    
                    async for chunk in response.content.iter_any():
                        if chunk:
                            handle_db_event(task_id, chunk, db)
                            decoded = chunk.decode('utf-8', errors='ignore')
                            yield decoded
                            
        except Exception as e:
            raise e

    
    return StreamingResponse(
        proxy(),
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "X-SSE-Proxy": "enabled",
            "X-Task-ID": task_id
        }
    )