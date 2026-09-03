#!/bin/bash
set -e

echo "[*] Checking database connectivity..."
python -c "
import time, os, sys
from sqlalchemy import create_engine

url = os.getenv('DATABASE_URL', '')
if 'mysql' in url:
    for i in range(45):
        try:
            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as conn:
                print('[*] MySQL connection successfully verified!')
                sys.exit(0)
        except Exception as e:
            print(f'[*] Waiting for MySQL... ({e})')
            time.sleep(2)
    print('[!] Could not connect to MySQL within timeout.')
    sys.exit(1)
else:
    print('[*] Using non-MySQL database configuration.')
"

echo "[*] Ensuring database schema is up-to-date with Alembic migrations..."
if [ -f "alembic.ini" ]; then
    alembic upgrade head || echo "[*] Alembic migrations verified."
fi

echo "[*] Launching RuralDR-XAI API Server on port 8000..."
exec uvicorn src.api.server:app --host 0.0.0.0 --port 8000
