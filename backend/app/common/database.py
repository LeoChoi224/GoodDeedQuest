from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, DeclarativeBase
from pathlib import Path
from config import get_setting

DATABASE_URL = str(get_setting().DATABASE_URL)
# Create engine
# SQLite test fallback or MySQL
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    echo=get_setting().DEBUG,
    connect_args=connect_args,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    with SessionLocal() as session:   # 각 개별 파일에서 개발 시 db.commit 안써도 됨 
        try:
            yield session              
            session.commit()           
        except Exception:
            session.rollback()        
            raise
        finally:
            session.close()           
