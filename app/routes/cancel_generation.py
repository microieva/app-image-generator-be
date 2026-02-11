import logging
import os
import sys
from dotenv import load_dotenv
from fastapi import APIRouter
import requests
from app.schemas.schemas import CancellationResponse
load_dotenv() 
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))    
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/cancel-generation/{task_id}", response_model=CancellationResponse)
async def cancel_generation(task_id:str):

    try:    
        cancel_response = requests.post(
            f"{settings.HF_SPACE_URL}/cancel-generation/{task_id}",
            headers={
                "Authorization": f"Bearer {settings.HF_TOKEN}"
            },
            timeout=10
        )
        
        if cancel_response.status_code == 200:
            return CancellationResponse(
                success=True,
                message=f"Generation task {task_id} cancelled successfully",
                task_id=task_id
            )
        else:
            return CancellationResponse(
                success=False,
                message=f"Failed to cancel generation task {task_id}. Status code: {cancel_response.status_code}",
                task_id=task_id
            )
    except Exception as e:
        logger.error(f"❌ Error cancelling generation task: {e}")
        import traceback
        traceback.print_exc()
        return CancellationResponse(
            success=False,
            message=f"Error cancelling generation task: {str(e)}",
            task_id=task_id
        )