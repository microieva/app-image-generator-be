from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
import os
import time
from dotenv import load_dotenv
from sqlalchemy.ext.declarative import declarative_base
from urllib.parse import quote_plus
import pyodbc

load_dotenv()

engine = None
SessionLocal = None
Base = declarative_base()

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

def create_database_if_not_exists():
    """Create the database if it doesn't exist"""

    db_user = os.getenv('DB_USER', 'sa')
    db_password = os.getenv('DB_PASSWORD')
    db_server = os.getenv('DB_SERVER', 'localhost')
    db_port = os.getenv('DB_PORT', '1433')
    db_name = os.getenv('DB_NAME', 'ImageGeneratorDB')
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
    db_user = os.getenv('DB_USER', 'sa')
    db_password = os.getenv('DB_PASSWORD')
    db_server = os.getenv('DB_SERVER', 'localhost')
    db_port = os.getenv('DB_PORT', '1433')
    db_name = os.getenv('DB_NAME', 'ImageGeneratorDB')
    drivers = [d for d in pyodbc.drivers() if 'ODBC Driver' in d and 'SQL Server' in d]
    driver_name = sorted(drivers)[-1] if drivers else 'ODBC Driver 17 for SQL Server'
    
    print(f"DB Server: {db_server}")
    print(f"DB Name: {db_name}")
    print(f"DB User: {db_user}")
    
    database_created = False
    
    for attempt in range(max_retries):
        try:
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
            
            print(f"🔌 Connection attempt {attempt + 1}/{max_retries}")
            
            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                echo=False
            )
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT DB_NAME()"))
                current_db = result.scalar()
                print(f"✅ Successfully connected to database: {current_db}")
                
                conn.execute(text("SELECT 1"))
            
            return engine
            
        except pyodbc.ProgrammingError as e:
            if '4060' in str(e) and not database_created:
                print(f"📋 Database not found error detected. Attempting to create database...")
                if create_database_if_not_exists(db_server, db_port, db_user, db_password, db_name, driver_name):
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
    db = get_session()
    try:
        yield db
    finally:
        db.close()

async def initialize_database():
    try:
        print("🔧 Initializing database connection...")
        engine = get_engine()
        print("✅ Database engine ready")
        
        try:
            from app.models.db_models import Task, Image
            print(f"-- 📋 Registered tables: {list(Base.metadata.tables.keys())}")
        except ImportError as e:
            print(f"❌ Could not import models: {e}")
            print("⚠️  Falling back to manual table creation...")
            return create_tables_manually(engine)
        
        print("🛠️ Creating tables with SQLAlchemy...")
        Base.metadata.create_all(bind=engine)
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"-- 📊 Tables in database: {tables}")
        
        if 'tasks' not in tables or 'images' not in tables:
            print("⚠️  SQLAlchemy creation failed, using manual fallback...")
            create_tables_manually(engine)
            tables = inspector.get_table_names()
        
        for table in ['tasks', 'images']:
            if table in tables:
                print(f"✅ Table '{table}' verified")
            else:
                print(f"❌ Table '{table}' not found!")
                
        return True
                
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

def create_tables_manually(engine):
    """Manual table creation fallback"""
    with engine.begin() as conn:
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='tasks' AND xtype='U')
            CREATE TABLE tasks (
                id INT IDENTITY(1,1) PRIMARY KEY,
                task_id NVARCHAR(36) UNIQUE NOT NULL,
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
                task_id NVARCHAR(36) UNIQUE NOT NULL,
                image_data NVARCHAR(MAX),
                prompt NVARCHAR(MAX),
                created_at DATETIME2 DEFAULT GETDATE(),
                CONSTRAINT FK_Image_Task FOREIGN KEY (task_id) 
                REFERENCES tasks(task_id) ON DELETE CASCADE
            )
        """))
        print("✅ Images table created/verified")