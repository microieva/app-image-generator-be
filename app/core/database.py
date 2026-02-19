import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
import time
from dotenv import load_dotenv
from sqlalchemy.ext.declarative import declarative_base
from urllib.parse import quote_plus

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.core.config import settings

load_dotenv()

engine = None
SessionLocal = None
Base = declarative_base()

IS_PRODUCTION = settings.is_production
IS_DEVELOPMENT = not IS_PRODUCTION

if IS_DEVELOPMENT:
    try:
        import pyodbc
    except ImportError:
        print("⚠️  pyodbc not installed - SQL Server support disabled")
        pyodbc = None
else:
    pyodbc = None

def get_engine():
    global engine
    if engine is None:
        engine = create_engine_with_retry()
    return engine

def get_session():
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return SessionLocal()

def create_prod_engine():
    """Create MySql engine for production"""
    db_user = settings.DB_USER
    db_password = settings.DB_PASSWORD
    db_host = settings.DB_SERVER
    db_port = settings.DB_PORT
    db_name = settings.DB_NAME
    
    print(f"🔧 Creating mysql connection...")
    print(f"   Host: {db_host}:{db_port}")
    print(f"   Database: {db_name}")
    print(f"   User: {db_user}")
    
    connection_string = f"mysql+pymysql://{db_user}:{quote_plus(db_password)}@{db_host}:{db_port}/{db_name}"
    
    engine = create_engine(
        connection_string,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
        pool_recycle=3600, 
        pool_pre_ping=True, 
        connect_args={
            'charset': 'utf8mb4',
            'ssl': {'ssl_disabled': True},
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5 
        }
    )
    
    return engine

def create_dev_engine():
    """Create SQL Server engine for development"""
    db_user = settings.DB_USER
    db_password = settings.DB_PASSWORD
    db_server = settings.DB_SERVER
    db_port = settings.DB_PORT
    db_name = settings.DB_NAME
    
    drivers = [d for d in pyodbc.drivers() if 'ODBC Driver' in d and 'SQL Server' in d]
    driver_name = sorted(drivers)[-1] if drivers else 'ODBC Driver 17 for SQL Server'
    
    print(f"🔧 Creating SQL Server connection...")
    print(f"   Server: {db_server}:{db_port}")
    print(f"   Database: {db_name}")
    print(f"   User: {db_user}")
    print(f"   Driver: {driver_name}")
    
    pyodbc_conn_str = (
        f'DRIVER={{{driver_name}}};'
        f'SERVER={db_server},{db_port};'
        f'DATABASE={db_name};'
        f'UID={db_user};'
        f'PWD={db_password};'
        f'TrustServerCertificate=yes;'
        f'Connection Timeout=30;'
    )
    
    odbc_connect_str = quote_plus(pyodbc_conn_str)
    connection_string = f"mssql+pyodbc://?odbc_connect={odbc_connect_str}"
    
    engine = create_engine(
        connection_string,
        pool_pre_ping=True,
        echo=False
    )
    
    return engine

def create_database_if_not_exists_sqlserver():
    """Create SQL Server database if it doesn't exist (development only)"""
    if IS_PRODUCTION:
        return True 
        
    db_user = settings.DB_USER
    db_password = settings.DB_PASSWORD
    db_server = settings.DB_SERVER
    db_port = settings.DB_PORT
    db_name = settings.DB_NAME
    
    drivers = [d for d in pyodbc.drivers() if 'ODBC Driver' in d and 'SQL Server' in d]
    driver_name = sorted(drivers)[-1] if drivers else 'ODBC Driver 17 for SQL Server'
    
    try:
        master_conn_str = (
            f'DRIVER={{{driver_name}}};'
            f'SERVER={db_server},{db_port};'
            f'DATABASE=master;'
            f'UID={db_user};'
            f'PWD={db_password};'
            f'TrustServerCertificate=yes;'
            f'Connection Timeout=30;'
        )
        
        print(f"🔧 Attempting to create database '{db_name}' if it doesn't exist...")
        
        master_engine = create_engine(f"mssql+pyodbc://?odbc_connect={quote_plus(master_conn_str)}")
        
        with master_engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sys.databases WHERE name = :db_name"), {'db_name': db_name})
            database_exists = result.fetchone()
            
            if not database_exists:
                print(f"📦 Creating database '{db_name}'...")
                conn.execute(text(f"CREATE DATABASE [{db_name}]"))
                conn.commit()
                print(f"✅ Database '{db_name}' created successfully!")
            else:
                print(f"✅ Database '{db_name}' already exists.")
                
        master_engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create database '{db_name}': {e}")
        return False

def create_engine_with_retry(max_retries=3, retry_delay=2):
    """Create engine with retry logic for both production and development"""
    
    if IS_PRODUCTION:
        print("🚀 PRODUCTION MODE: Using mysql")
        return create_prod_engine()
    else:
        print("🔧 DEVELOPMENT MODE: Using SQL Server")
        database_created = False
        
        for attempt in range(max_retries):
            try:
                engine = create_dev_engine()
                
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT DB_NAME()"))
                    current_db = result.scalar()
                    print(f"✅ Successfully connected to database: {current_db}")
                    conn.execute(text("SELECT 1"))
                
                return engine
                
            except pyodbc.ProgrammingError as e:
                if '4060' in str(e) and not database_created:
                    print(f"📋 Database not found error detected. Attempting to create database...")
                    if create_database_if_not_exists_sqlserver():
                        database_created = True
                        if attempt < max_retries - 1:
                            print(f"🔄 Retrying connection with newly created database...")
                            continue
                        else:
                            print("💥 Failed to connect even after creating database")
                            raise
                    else:
                        print("💥 Failed to create database")
                        raise
                else:
                    print(f"❌ Connection attempt {attempt + 1}/{max_retries} failed: {e}")
                    if attempt < max_retries - 1:
                        print(f"⏳ Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        print("💥 All connection attempts failed")
                        raise
                        
            except Exception as e:
                print(f"❌ Connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("💥 All connection attempts failed")
                    raise

def get_db():
    """Dependency for FastAPI endpoints (unchanged interface)"""
    db = get_session()
    try:
        yield db
    finally:
        db.close() 

async def initialize_database():
    try:
        if IS_PRODUCTION:
            print("🚀 Initializing production database (mysql)...")
        else:
            print("🔧 Initializing development database (SQL Server)...")
            
        engine = get_engine()
        print("✅ Database engine ready")
        
        try:
            from app.models.db_models import Task, Image
            print(f"-- 📋 Registered tables: {list(Base.metadata.tables.keys())}")
            use_sqlalchemy = True
        except ImportError as e:
            print(f"❌ Could not import models: {e}")
            print("⚠️  Falling back to manual table creation...")
            use_sqlalchemy = False
        
        if use_sqlalchemy:
            print("🛠️ Creating tables with SQLAlchemy...")
            Base.metadata.create_all(bind=engine)
            
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"-- 📊 Tables in database: {tables}")
            
            required_tables = {'tasks', 'images'}
            existing_tables = set(table.lower() for table in tables)
            
            missing_tables = required_tables - existing_tables
            
            if missing_tables:
                print(f"⚠️  SQLAlchemy creation incomplete. Missing: {missing_tables}")
                print("   Using manual table creation fallback...")
                use_sqlalchemy = False
        
        if not use_sqlalchemy:
            print("🛠️ Creating tables manually...")
            if IS_PRODUCTION:
                create_prod_db_tables(engine)
            else:
                create_tables_manually(engine)
            
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"-- 📊 Tables in database: {tables}")
        
        print("🔍 Verifying all required tables exist...")
        required_tables = ['tasks', 'images']
        tables_lower = [table.lower() for table in tables]
        
        all_tables_exist = True
        for table in required_tables:
            if table in tables_lower:
                print(f"✅ Table '{table}' verified")
            else:
                print(f"❌ Table '{table}' not found!")
                all_tables_exist = False
        
        if IS_DEVELOPMENT:
            print("🔍 Detailed table check for development...")
            with engine.connect() as conn:
                try:
                    conn.execute(text("SELECT TOP 1 * FROM tasks"))
                    print("✅ Tasks table accessible")
                except Exception as e:
                    print(f"⚠️  Tasks table issue: {e}")
                 
                try:
                    conn.execute(text("SELECT TOP 1 * FROM images"))
                    print("✅ Images table accessible")
                except Exception as e:
                    print(f"⚠️  Images table issue: {e}")
        
        elif IS_PRODUCTION:
            print("🔍 Detailed table check for production...")
            with engine.connect() as conn:
                try:
                    conn.execute(text("SELECT * FROM tasks LIMIT 1"))
                    print("✅ Tasks table accessible")
                except Exception as e:
                    print(f"⚠️  Tasks table issue: {e}")
                
                try:
                    conn.execute(text("SELECT * FROM images LIMIT 1"))
                    print("✅ Images table accessible")
                except Exception as e:
                    print(f"⚠️  Images table issue: {e}")
        
        if all_tables_exist:
            print("🎉 Database initialization completed successfully!")
        else:
            print("⚠️  Database initialization completed with warnings")
        
        return all_tables_exist
                
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        # Re-raise to stop the application if initialization fails
        raise

def create_tables_manually(engine):
    """Manual table creation fallback"""
    with engine.begin() as conn:
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='tasks' AND xtype='U')
            CREATE TABLE tasks (
                id INT IDENTITY(1,1) PRIMARY KEY,
                task_id NVARCHAR(36) UNIQUE NOT NULL,
                prompt NVARCHAR(MAX),
                status NVARCHAR(20) DEFAULT 'pending',
                progress INT DEFAULT 0,
                created_at DATETIME2 DEFAULT GETDATE(),
                updated_at DATETIME2 NULL
            )
        """))
        print("✅ Tasks table created/verified")
        
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='images' AND xtype='U')
            CREATE TABLE images (
                id INT IDENTITY(1,1) PRIMARY KEY,
                task_id NVARCHAR(36) NULL,
                image_data NVARCHAR(MAX),
                prompt NVARCHAR(MAX),
                created_at DATETIME2 DEFAULT GETDATE(),
                CONSTRAINT FK_Image_Task FOREIGN KEY (task_id) 
                REFERENCES tasks(task_id) ON DELETE SET NULL
            )
        """))
        print("✅ Images table created/verified")

def create_prod_db_tables(engine):
    """MySQL table creation for production"""
    with engine.begin() as conn:
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id VARCHAR(36) UNIQUE NOT NULL,
                prompt LONGTEXT,
                status VARCHAR(20) DEFAULT 'pending',
                progress INT DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NULL,
                INDEX idx_tasks_task_id (task_id),
                INDEX idx_tasks_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        print("✅ Tasks table created/verified")
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS images (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id VARCHAR(36) NULL,
                image_data LONGTEXT,
                prompt LONGTEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_images_task_id (task_id),
                CONSTRAINT fk_image_task FOREIGN KEY (task_id) 
                REFERENCES tasks(task_id) ON DELETE SET NULL ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        print("✅ Images table created/verified")
        
        inspector = inspect(engine)
        
        indexes = inspector.get_indexes('tasks')
        existing_index_names = {idx['name'] for idx in indexes}
        
        if 'idx_tasks_created_at' not in existing_index_names:
            conn.execute(text("CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC)"))
            print("✅ Created index: idx_tasks_created_at")
        
        indexes = inspector.get_indexes('images')
        existing_index_names = {idx['name'] for idx in indexes}
        
        if 'idx_images_created_at' not in existing_index_names:
            conn.execute(text("CREATE INDEX idx_images_created_at ON images(created_at DESC)"))
            print("✅ Created index: idx_images_created_at")
        
        print("✅ All indexes created/verified")