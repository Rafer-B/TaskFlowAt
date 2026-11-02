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

After configuring `taskflow-backend/.env` and applying the migrations, start
the API in a separate terminal, from the same directory:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Keep it running while using the frontend. The default frontend API address is
`http://127.0.0.1:8000`.

If the database already contains these tables, back it up and compare its schema
with `migrations/versions/20261030_0001_initial_schema.py` before proceeding.
`alembic upgrade head` is for an empty database. Only when the existing schema
already matches the original schema, initialize tracking at
`20261030_0002` with `alembic stamp 20261030_0002`, then run
`alembic upgrade head` so the user-role migration is applied. Stamping does not
create or alter tables.

## Perfis e autenticação

The API uses bearer tokens. Add a private key of at least 32 characters to
`taskflow-backend/.env` (do not commit it):

```dotenv
TASKFLOW_JWT_SECRET=replace-with-a-private-random-value-at-least-32-characters
TASKFLOW_INITIAL_ADMIN_EMAIL=admin@example.com
```

Generate a key locally with
`python -c "import secrets; print(secrets.token_urlsafe(48))"`.
Apply the role migration with `alembic upgrade head`. Existing accounts are
assigned the `member` profile by default. To promote the chosen account after
migration, run `python -m app.bootstrap_admin` from this directory. If the
configured email does not exist yet, the command interactively creates the
first administrator and hashes the password locally. This explicit command is
the only unauthenticated bootstrap path; do not expose it as an API endpoint.

Administrators can access both offices, create accounts and assign either
profile. Members can only access the front-office and update the status of
tasks assigned to them. Role authorization is enforced by FastAPI as well as by
the frontend route middleware.

## Registo de trabalho e anexos

Na página `/my-work`, abra **Registar trabalho** numa tarefa para guardar uma
nota, atualizar o progresso e consultar o histórico. Pode anexar até cinco
ficheiros por registo, com um máximo de 10 MB por ficheiro e 25 MB no total.
São aceites PDF, PNG/JPG/WEBP, TXT, MD, CSV, DOCX e XLSX.

Os registos ficam associados ao utilizador autenticado. Apenas um
administrador ou o membro atribuído à tarefa pode consultar o histórico e
descarregar os anexos. Os ficheiros são guardados em
`taskflow-backend/task_attachments`, fora da pasta pública `/uploads`, e os
downloads passam por uma rota autenticada. A migração `20261102_0004` adiciona
o progresso e as tabelas do histórico; aplique-a com `alembic upgrade head`.

## Nuxt 4

Set `NUXT_PUBLIC_API_BASE` to the URL where this FastAPI service is reachable.
For local development, the default is `http://127.0.0.1:8000`. For example:

```dotenv
NUXT_PUBLIC_API_BASE=http://127.0.0.1:8000
```

Nuxt makes requests to this API; PostgreSQL credentials stay in the backend
environment and are never exposed to the frontend.
