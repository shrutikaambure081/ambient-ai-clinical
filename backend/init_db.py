"""
One-off script to (re)create all database tables from the SQLAlchemy
models. Run with: `python init_db.py` after configuring DATABASE_URL.

Requires the pgvector extension to be enabled on the target Postgres
database: `CREATE EXTENSION IF NOT EXISTS vector;`
"""
from app.database import Base, engine
from app import models  # noqa: F401  (ensures models are registered)

if __name__ == "__main__":
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")
