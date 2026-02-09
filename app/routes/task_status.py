
from fastapi import APIRouter, Depends, HTTPException
from requests import Session
from app.events.db_events import  get_task_info
from app.models.db_models import TaskStatus
from app.schemas.schemas import TaskStatusResponse
from app.core.database import get_db

router = APIRouter()

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_generation_status(task_id: str, db: Session = Depends(get_db)):
    try:
        task_info = get_task_info(task_id, db)

        task_data = {
            'task_id': task_id,
            'status': task_info.status,
            'progress': task_info.progress,
            'created_at': task_info.created_at,
            'cancelled': task_info.status == TaskStatus.CANCELLED,
            'prompt': task_info.prompt
        }
    
        return TaskStatusResponse(**task_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={"message": f"Failed to fetch task status: {str(e)}"}
        )