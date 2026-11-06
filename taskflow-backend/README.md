# Backend do TaskFlow

O backend do TaskFlow é uma API desenvolvida com **FastAPI**. Serve os dados
utilizados pelo frontend Nuxt 4 e comunica com a base de dados **PostgreSQL**.
O navegador comunica apenas com a API: nunca deve ligar diretamente à base de
dados.

## Requisitos

- Python 3.10 ou superior;
- PostgreSQL;
- dependências listadas em `requirements.txt`.

Os comandos abaixo devem ser executados a partir da pasta `taskflow-backend`.
No Windows, se utilizar o ambiente virtual local `.venv`, invoque os comandos
Python e Alembic através de `.venv\Scripts\python.exe` e
`.venv\Scripts\alembic.exe`, respectivamente.

## Configuração do PostgreSQL

Crie a base de dados `taskflowdb_at` no PostgreSQL. Depois, crie o ficheiro
`.env` nesta pasta com as credenciais da base de dados:

```dotenv
# Endereço e porta do servidor PostgreSQL
DB_HOST=localhost
DB_PORT=5432

# Nome da base de dados e credenciais de acesso
DB_NAME=taskflowdb_at
DB_USER=utilizador_postgres
DB_PASSWORD=palavra-passe_postgres
```

O ficheiro `.env` contém credenciais privadas e não deve ser enviado para o
Git. Substitua os valores de exemplo pelos dados do seu ambiente.

## Instalação e migrações

Instale as dependências e aplique as migrações para criar ou atualizar o
esquema da base de dados:

```bash
python -m pip install -r requirements.txt
alembic upgrade head
```

No Windows, com o ambiente virtual `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\alembic.exe upgrade head
```

`alembic upgrade head` aplica, pela ordem definida, todas as migrações até à
versão mais recente. As migrações são incrementais: acrescentam ou alteram
tabelas e colunas sem recriar a base de dados. Antes de atualizar uma base de
dados com informação importante, faça uma cópia de segurança.

As migrações atuais acrescentam:

| Revisão | Alteração |
| --- | --- |
| `20261030_0001` | Estrutura inicial: utilizadores, projetos, membros de projetos e tarefas. |
| `20261030_0002` | Preparação dos dados iniciais previstos para a aplicação. |
| `20261102_0003` | Perfis da plataforma e autenticação. |
| `20261102_0004` | Progresso das tarefas, registos de trabalho e metadados dos anexos. |
| `20261102_0005` | Papéis de colaborador e observador nos projetos. |
| `20261102_0006` | Eventos persistentes do calendário. |
| `20261102_0007` | Equipas, membros de equipa e associação de projetos a equipas. |
| `20261106_0008` | Associação normalizada de responsáveis por tarefa; preserva as atribuições existentes. |
| `20261106_0009` | Limita cada tarefa a um responsável e preserva a atribuição principal. |

### Base de dados que já contém tabelas

Não execute a migração inicial numa base de dados existente sem confirmar
primeiro o respetivo esquema. Compare a estrutura com
`migrations/versions/20261030_0001_initial_schema.py` e faça uma cópia de
segurança.

Se a base de dados já corresponder integralmente à estrutura inicial, mas ainda
não tiver histórico de migrações, pode iniciar o registo no Alembic com:

```bash
alembic stamp 20261030_0002
alembic upgrade head
```

O comando `stamp` apenas regista uma revisão no histórico do Alembic; **não**
cria, altera ou valida tabelas. Não o utilize para contornar erros de migração
ou sem confirmar que o esquema existente corresponde à revisão indicada.

Para consultar a revisão aplicada e a mais recente disponível:

```bash
alembic current
alembic heads
```

## Iniciar a API

Depois de configurar o `.env` e aplicar as migrações, inicie o servidor na
pasta `taskflow-backend`:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Mantenha este processo em execução enquanto utiliza o frontend. Em
desenvolvimento, a API fica disponível em `http://127.0.0.1:8000`. A
documentação interativa dos endpoints encontra-se em
`http://127.0.0.1:8000/docs`.

## Perfis e autenticação

A API utiliza tokens **Bearer** para autenticar pedidos. Configure no `.env`
uma chave JWT privada com, pelo menos, 32 caracteres:

```dotenv
# Chave privada usada para assinar os tokens de acesso
TASKFLOW_JWT_SECRET=substitua-por-uma-chave-aleatoria-com-pelo-menos-32-caracteres

# Email da conta escolhida para ser o primeiro administrador
TASKFLOW_INITIAL_ADMIN_EMAIL=admin@example.com
```

Pode gerar uma chave aleatória localmente:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Não partilhe nem envie esta chave para o Git. Depois de aplicar a migração
`20261102_0003`, execute o comando de configuração do administrador:

```bash
python -m app.bootstrap_admin
```

O comando promove a conta indicada por `TASKFLOW_INITIAL_ADMIN_EMAIL`. Se essa
conta ainda não existir, pede os dados necessários e guarda a palavra-passe sob
a forma de hash. Este é o único processo previsto para criar o primeiro
administrador sem uma sessão autenticada; não o disponibilize como endpoint da
API.

### Perfis da plataforma

- **Administrador:** pode aceder ao back-office e ao front-office, criar contas
  e gerir os perfis da plataforma.
- **Utilizador:** acede ao front-office e às funcionalidades permitidas pelos
  papéis que tem nos projetos.

### Papéis nos projetos

- **Responsável (`owner`):** gere o projeto, os membros e os respetivos papéis;
  pode criar e gerir tarefas.
- **Colaborador (`contributor`):** pode trabalhar nas tarefas do projeto,
  criá-las e documentar o trabalho.
- **Observador (`viewer`):** pode consultar as tarefas e o histórico, mas não
  pode alterar o projeto ou as tarefas nem ser atribuído a tarefas.

Cada tarefa tem um único responsável, escolhido pelo administrador ou pelo
responsável do projeto entre os membros ativos que não sejam observadores. A
associação é criada pela migração `20261106_0008`; a migração
`20261106_0009` preserva o responsável principal e impõe o limite de um
responsável por tarefa.

Qualquer utilizador autenticado pode criar um projeto e passa a ser o seu
responsável. Apenas administradores podem eliminar projetos definitivamente;
os responsáveis podem arquivá-los. A API valida as permissões em cada pedido:
ocultar um botão no frontend não substitui esta validação.

As contas têm de ser criadas por um administrador antes de poderem ser
adicionadas a projetos ou equipas. A migração `20261102_0005` converte os
antigos papéis `member` em `contributor`.

## Registos de trabalho e anexos

Na página `/my-work`, um utilizador pode registar uma nota de trabalho,
atualizar o progresso de uma tarefa e consultar o histórico. Cada registo pode
incluir até cinco anexos, com um limite de 10 MB por ficheiro e 25 MB no total.
São aceites ficheiros PDF, PNG, JPG, WEBP, TXT, MD, CSV, DOCX e XLSX.

Os registos ficam associados à tarefa e ao utilizador autenticado. A consulta
do histórico e a transferência dos anexos exigem autorização na API. Os
ficheiros são guardados em `task_attachments`, fora da pasta pública
`/uploads`; o acesso é feito por endpoints autenticados. A migração
`20261102_0004` acrescenta o progresso e as tabelas necessárias ao histórico.

## Calendário e eventos

O endpoint autenticado `/calendar/events/` permite consultar e gerir eventos
pessoais ou associados a projetos. Cada utilizador vê os seus eventos pessoais
e os eventos dos projetos a que pertence. Os administradores podem gerir todos
os eventos.

Um responsável ou colaborador pode criar um evento associado a um projeto.
O criador ou um administrador pode gerir o evento; nos eventos de projeto, o
responsável do projeto também pode editá-lo ou eliminá-lo. Os eventos pessoais
só podem ser geridos pelo seu criador ou por um administrador. A migração
`20261102_0006` cria a tabela dos eventos.

## Equipas

As equipas permitem reunir utilizadores e associar projetos. Cada projeto pode
estar associado a, no máximo, uma equipa. Administradores e responsáveis de
projetos podem criar equipas; os administradores, os criadores da equipa e os
responsáveis dos projetos associados podem geri-la, conforme a operação.

Os membros de uma equipa não são adicionados automaticamente aos projetos
associados e não recebem permissões de projeto por essa associação. A
participação e os papéis no projeto continuam a ser geridos separadamente em
**Projetos → Membros**. A migração `20261102_0007` cria as tabelas de equipas e
membros e acrescenta a associação opcional de equipa aos projetos.

## Ligação ao frontend Nuxt 4

O frontend deve apontar para o endereço onde a API está disponível. Em
desenvolvimento local, o valor predefinido é `http://127.0.0.1:8000`. Configure
`NUXT_PUBLIC_API_BASE` no ambiente do frontend, se necessário:

```dotenv
NUXT_PUBLIC_API_BASE=http://127.0.0.1:8000
```

As credenciais do PostgreSQL e a chave JWT pertencem apenas ao ambiente do
backend. Não as inclua na configuração pública do Nuxt, pois os valores
`NUXT_PUBLIC_*` podem ser expostos ao navegador.
