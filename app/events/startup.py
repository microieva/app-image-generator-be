from app.core.config import settings
from app.core.database import Base, get_engine, create_postgresql_engine, create_sqlserver_engine

async def start_up():
    try:
        if settings.is_development:
            print("⚙️ Running in development mode")
            create_sqlserver_engine()
        else:
            create_postgresql_engine()

        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
