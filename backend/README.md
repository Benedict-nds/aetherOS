# AetherQore backend

Local FastAPI + PostgreSQL. You need Python 3.11+ and a running PostgreSQL instance.

After the API is running:
- Health: http://127.0.0.1:8000/health
- Docs: http://127.0.0.1:8000/docs

## Setup

```bash
cd backend

# 1) Create virtual environment
python -m venv env

# 2) Activate venv
# Windows:
env\Scripts\activate
# Mac/Linux:
source env/bin/activate

# 3) Install dependencies
pip install -r requirements.txt

# 4) Create local env file
# Mac/Linux:
cp .env.example .env
# Windows:
copy .env.example .env

# 5) Ensure PostgreSQL is running and the database exists
# Example (local Homebrew PostgreSQL):
# createdb aetherqore
# Or use Docker if available:
# docker compose up -d

# 6) Run migrations
alembic upgrade head

# 7) Start API
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

On startup, the API seeds a demo admin user if one does not already exist.

## Authentication

Demo credentials (development only):

- Email: `admin@aetherqore.local`
- Password: `Admin123!`

**Change this password before any real pharmacy use.**

JWT access tokens expire after **8 hours**.

### Login

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@aetherqore.local","password":"Admin123!"}'
```

Example response:

```json
{
  "success": true,
  "data": {
    "access_token": "<jwt>",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "full_name": "Pharmacy Admin",
      "email": "admin@aetherqore.local",
      "username": "admin",
      "role": "owner"
    }
  },
  "message": "Logged in",
  "errors": []
}
```

Save the `access_token` from the response.

### Current user

```bash
curl http://127.0.0.1:8000/api/auth/me \
  -H "Authorization: Bearer <TOKEN>"
```

### Logout

```bash
curl -X POST http://127.0.0.1:8000/api/auth/logout \
  -H "Authorization: Bearer <TOKEN>"
```

For this MVP, logout is client-side: delete the stored token after a successful logout response. Tokens are not blacklisted on the server.

## Tests

```bash
pytest
```
