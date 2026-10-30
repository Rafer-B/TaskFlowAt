# TaskFlow Backend

FastAPI serves the API used by the Nuxt 4 frontend. The backend connects to
PostgreSQL; the browser frontend should use the API and must not connect to the
database directly.

## PostgreSQL configuration

Create the database `taskflowdb_at`, then configure these values in
`taskflow-backend/.env`:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=taskflowdb_at
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password
```

Install the backend dependencies and apply the schema:

```bash
python -m pip install -r requirements.txt
alembic upgrade head
```

Run both commands from the `taskflow-backend` directory. The initial migration
creates `users`, `projects`, `project_members`, and `tasks`, including their
primary keys, identity columns, defaults, unique email constraint, and foreign
keys.

If the database already contains these tables, back it up and compare its schema
with `migrations/versions/20261030_0001_initial_schema.py` before proceeding.
`alembic upgrade head` is for an empty database. Only when the existing schema
already matches the migration, initialize migration tracking with
`alembic stamp head`; stamping does not create or alter tables.

## Nuxt 4

Set `NUXT_PUBLIC_API_BASE` to the URL where this FastAPI service is reachable.
For local development, the default is `http://127.0.0.1:8000`. For example:

```dotenv
NUXT_PUBLIC_API_BASE=http://127.0.0.1:8000
```

Nuxt makes requests to this API; PostgreSQL credentials stay in the backend
environment and are never exposed to the frontend.
