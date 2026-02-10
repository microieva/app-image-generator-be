from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging


logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Application starting up...")
    from app.core.shutdown_manager import shutdown_manager 
    from app.core.scheduler import TaskScheduler
    from app.events.cleanup import db_weekly_cleanup, midnight_cleanup 
    from app.core.database import initialize_database

    app.state.scheduler = TaskScheduler() 

    await initialize_database()

    app.state.scheduler.start_midnight_scheduler(app, midnight_cleanup)
    app.state.scheduler.start_weekly_scheduler(app, db_weekly_cleanup)
    
    logger.info("✅ Application startup complete")
    
    yield  

    logger.info("🛑 Application shutting down...")
    if hasattr(app.state, 'scheduler'):
        app.state.scheduler.shutdown_scheduler()
    
    await shutdown_manager.run_cleanup()
    
    logger.info("✅ Application shutdown complete")