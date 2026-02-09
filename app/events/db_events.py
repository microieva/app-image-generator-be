import datetime
from sqlalchemy import update
from app.schemas.schemas import GenerationResult, TaskData
from app.core.database import get_db
from app.models.db_models import Image, Task
from sqlalchemy.orm import Session, joinedload


def save_task_to_db(task_info, db: Session):
    try:
        task = Task(
            task_id=task_info['task_id'],
            status=task_info['status'],
            progress=task_info['progress'],
            prompt=task_info['prompt'],
            updated_at=datetime.datetime.now()
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        return task
    except Exception as e:
        db.rollback()
        print(f"Error saving task: {e}")

def update_task_in_db(task_id:str, task_updates, db:Session):
    try:
        updates = (
            update(Task)
            .where(Task.task_id == task_id)
            .values(**task_updates)
        )
        result = db.execute(updates)
        db.commit()
        
        if result.rowcount == 0:
            print(f"⚠️ No task found with ID: {task_id}")
            return False
            
        print(f"✅ Updated task {task_id}")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating task {task_id}: {e}")
        return False

def save_image_to_db(result: GenerationResult, db: Session):
    try:
        image = Image(
            task_id=result.task_id,   
            image_data=result.image_data, 
            prompt=result.prompt        
        )
        db.add(image)
        db.commit()
        db.refresh(image)
        print(f"✅ Image saved for task {result.task_id}")
        return True
    except Exception as e:
        db.rollback()
        print(f"Error saving image: {e}")
        import traceback
        traceback.print_exc()
        return False

def delete_image_from_db(task_id: str):
    db_gen = get_db()
    try:
        db = next(db_gen) 
        image = db.query(Image).filter(Image.task_id == task_id).first()
        
        if image:
            db.delete(image)
            print(f"✅ Image with task_id {task_id} deleted successfully")
            return True
        else:
            print(f"⚠️  No image found with task_id {task_id}")
            return False
                
    except Exception as e:
        print(f"❌ Error deleting image with task_id {task_id}: {e}")
        return False
    
def delete_all_tasks():
    db_gen = get_db()
    try:
        db = next(db_gen) 
        deleted_tasks = db.query(Task).delete()
        db.commit()
        print(f"✅ Deleted {deleted_tasks} tasks successfully")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error deleting all tasks: {e}")
        return False
    

def get_all_tasks(db: Session):
    try:
        tasks = db.query(Task).options(joinedload(Task.image)).all()
        
        task_dict = {}
        for task in tasks:    
            task_dict[task.task_id] = {
                "status": task.status,
                "progress": task.progress or 0,
                "prompt": task.prompt, 
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "task_id": task.task_id
            }
        
        return task_dict
        
    except Exception as e:
        print(f"Error retrieving tasks: {e}")
        return {}
    
def get_task_info(task_id: str, db: Session):
    try:
        task = db.query(Task).options(joinedload(Task.image)).filter(Task.task_id == task_id).first()
        
        if not task:
            print(f"⚠️ No task found with ID: {task_id}")
            return None

        task = {
            "status": task.status,
            "progress": task.progress or 0,
            "prompt": task.prompt, 
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "task_id": task.task_id
        }
        
        return TaskData(**task)
        
    except Exception as e:
        print(f"Error retrieving task info for {task_id}: {e}")
        return None
