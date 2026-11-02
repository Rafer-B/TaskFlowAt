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
platform profile. Any authenticated user can access the collaborative workspace
and create a project; its creator becomes the project owner. Project owners can
edit and archive their projects, add registered users to the team, manage
project roles, create tasks and assign them to project members. Contributors
can create and manage project tasks and document work. Viewers can consult
project tasks and their history but cannot modify them or be assigned tasks.
Only platform administrators can permanently delete projects; project owners
can archive them instead. Project membership and role authorization are
enforced by the API.

The project member selector lists active registered accounts that are not
already part of the project. New accounts must first be created by a platform
administrator; an unknown email cannot be added as a project member.

Apply migration `20261102_0005` with `alembic upgrade head` to add contributor
and viewer roles. Existing project `member` roles are migrated to
`contributor`.

## Calendário e eventos

The authenticated calendar endpoint is `/calendar/events/`. Users can create
personal events or share events with a project where they are an owner or
contributor. Users see their own personal events and events for projects they
belong to; administrators can manage all events. Event creators and project
owners can update or delete project events, while personal events can only be
managed by their creator or an administrator.

Apply migration `20261102_0006` with `alembic upgrade head` to create the
calendar events table.

## Equipas

As equipas do workspace podem reunir membros e ter vários projetos associados;
cada projeto pode pertencer a uma equipa. Administradores e responsáveis de
projetos podem criar e gerir equipas. Os membros de uma equipa não são
adicionados automaticamente aos projetos associados, nem recebem permissões
de projeto; essas permissões continuam a ser geridas em **Projetos → Membros**.
Os membros da equipa e os membros dos projetos associados podem consultar a
equipa. Aplique a migração `20261102_0007` com `alembic upgrade head`.

## Registo de trabalho e anexos

Na página `/my-work`, abra **Registar trabalho** numa tarefa para guardar uma
nota, atualizar o progresso e consultar o histórico. Pode anexar até cinco
ficheiros por registo, com um máximo de 10 MB por ficheiro e 25 MB no total.
São aceites PDF, PNG/JPG/WEBP, TXT, MD, CSV, DOCX e XLSX.

Os registos ficam associados ao utilizador autenticado. Apenas um
administrador ou membro do projeto pode consultar o histórico e descarregar os
anexos. Os ficheiros são guardados em
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
