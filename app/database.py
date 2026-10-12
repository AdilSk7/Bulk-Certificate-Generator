import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./certificates.db")

connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

from sqlalchemy import inspect, text

def run_migrations(target_engine=None):
    eng = target_engine or engine
    inspector = inspect(eng)
    if "generation_jobs" in inspector.get_table_names():
        columns = {col["name"] for col in inspector.get_columns("generation_jobs")}
        new_columns = [
            ("certificate_title", "VARCHAR", "'CERTIFICATE OF PARTICIPATION'"),
            ("introduction_text", "VARCHAR", "'This certificate is proudly presented to'"),
            ("description_text", "VARCHAR", "'for successfully participating in'"),
            ("presented_by_label", "VARCHAR", "'Presented by'"),
        ]
        with eng.connect() as conn:
            for col_name, col_type, default_val in new_columns:
                if col_name not in columns:
                    conn.execute(text(f"ALTER TABLE generation_jobs ADD COLUMN {col_name} {col_type} DEFAULT {default_val}"))
            conn.commit()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
