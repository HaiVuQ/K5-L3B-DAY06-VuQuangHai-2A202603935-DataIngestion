"""Read-only setup check; this is a utility, not the student pipeline solution."""
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(Path(__file__).resolve().parents[1] / '.env')
vector_store_mode = os.getenv('VECTOR_STORE', 'qdrant_local')
url = os.getenv('DATABASE_URL')

pg_ok = False
if url:
    try:
        with psycopg.connect(url, connect_timeout=3) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database(), current_setting('server_version'), extversion FROM pg_extension WHERE extname = 'vector'")
                row = cursor.fetchone()
                if row:
                    print(f'Database: {row[0]} | PostgreSQL: {row[1]} | pgvector: {row[2]}')
                    pg_ok = True
    except psycopg.Error:
        pass

if not pg_ok:
    try:
        from qdrant_client import QdrantClient
        qdrant_path = ROOT_DIR / os.getenv('QDRANT_PATH', 'data/qdrant_storage')
        qdrant_path.mkdir(parents=True, exist_ok=True)
        client = QdrantClient(path=str(qdrant_path))
        collections = [c.name for c in client.get_collections().collections]
        client.close()
        print(f'Vector Store: Qdrant Local (persistent path: {qdrant_path}) | Collections: {collections}')
    except Exception as exc:
        sys.exit(f'Database connection failed ({exc}). Check Docker/PostgreSQL or Qdrant setup in starter/.env.')

print('Setup OK.')

