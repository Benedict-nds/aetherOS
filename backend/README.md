# AetherQore backend

Local FastAPI + PostgreSQL. You need Python 3.11+ and Docker Desktop.

After the API is running:
- Health: http://127.0.0.1:8000/health
- Docs: http://127.0.0.1:8000/docs

Stop the database: `docker compose down`

## Setup
cd backend

# 1) Create virtual environment
python -m venv .venv

# 2) Activate venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 3) Install dependencies
pip install -r requirements.txt

# 4) Create local env file
copy .env.example .env
# Mac/Linux: cp .env.example .env

# 5) Start Postgres
docker compose up -d

# 6) Run migrations
alembic upgrade head

# 7) Start API
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000