
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.events.db_events import delete_all_tasks, get_all_tasks
from app.schemas.schemas import DeletionResponse


router = APIRouter()

@router.delete("/delete-tasks")
async def delete_tasks():
    ongoing_tasks = get_all_tasks()

    try:
        if not ongoing_tasks or len(ongoing_tasks) == 0:
            return DeletionResponse(
                success=False,
                message=f"No tasks found to delete"
            )
        
        total_tasks = len(ongoing_tasks)
        delete_all_tasks()
        
        return DeletionResponse(
            success=True,
            message=f"Deleted {total_tasks} tasks successfully"
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Failed to delete tasks: {str(e)}"}
        )
