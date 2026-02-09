from fastapi import APIRouter, Depends
from app.schemas.schemas import TaskData, TasksResponse
from app.events.db_events import get_all_tasks
from app.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/tasks", response_model=TasksResponse)
def get_tasks(db: Session = Depends(get_db)):
    all_tasks = get_all_tasks(db)

    if not all_tasks:
        return TasksResponse(
            total_tasks=0,
            tasks=None  
        )
    
    
    task_list = []
    
    for task_id, task_data in all_tasks.items():
        status = task_data['status']
        progress = task_data['progress']
        prompt = task_data['prompt']
        created_at = task_data['created_at']
        updated_at = task_data['updated_at']

        task_response = TaskData(
            task_id=task_id, 
            progress=int(progress),
            status=status,
            prompt=prompt,
            created_at=created_at,
            updated_at=updated_at
        )
        
        task_list.append(task_response)

    return TasksResponse(
        total_tasks=len(task_list),
        tasks=task_list
    )
