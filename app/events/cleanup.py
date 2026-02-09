from fastapi import FastAPI
from sqlalchemy import delete
from datetime import datetime
from app.events.db_events import delete_all_tasks
from app.models.db_models import Image, Task
from app.core.database import get_session
import logging

logger = logging.getLogger(__name__)

async def midnight_cleanup(app: FastAPI):
    logger.info("🕛 Starting midnight cleanup...")

    try:
        success = delete_all_tasks()
        logger.info(f"Midnight cleanup - Database: {success}")
    except Exception as e:
        logger.error(f"Midnight cleanup - Database cleanup failed: {e}")
    
    result = {
        "message": "Midnight cleanup completed",
        "timestamp": datetime.now().isoformat(),
    }
    
    logger.info(f"✅ Midnight cleanup completed: {result}")
    return result

async def db_weekly_cleanup(app: FastAPI):
    logger.info("🗓️ Starting weekly database cleanup...")
    
    results = {}
    
    try:
        async with get_session() as session:
            stmt_images = delete(Image)
            result_images = await session.execute(stmt_images)
            
            stmt_tasks = delete(Task)
            result_tasks = await session.execute(stmt_tasks)
            
            await session.commit()
            
            results["images_deleted"] = result_images.rowcount
            results["tasks_deleted"] = result_tasks.rowcount
            results["timestamp"] = datetime.now().isoformat()
            
    except Exception as e:
        logger.error(f"Error during weekly database cleanup: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()
    
    logger.info(f"✅ Weekly cleanup completed: {results}")
    return results
