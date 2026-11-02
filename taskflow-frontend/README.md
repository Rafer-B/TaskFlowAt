# Nuxt Minimal Starter

The frontend communicates with the TaskFlow FastAPI backend. Configure its URL
with `NUXT_PUBLIC_API_BASE` (for example, `http://127.0.0.1:8000`). PostgreSQL
credentials belong only in the backend environment; do not put them in Nuxt
runtime configuration.

## Área de trabalho (front-office)

O caminho `/my-work` apresenta a área operacional dos membros: tarefas
atribuídas, prazos, progresso, pesquisa/filtros e atualização do estado da
tarefa. A página consome os endpoints `/users/`, `/projects/` e
`/tasks/?assigned_to=<id>` da API.

O front-office utiliza a sessão autenticada para identificar o membro e mostrar
apenas o seu trabalho.

Os IDs de utilizadores, projetos e tarefas são gerados pelo PostgreSQL
(`Identity`). Ao criar projetos ou tarefas, o campo `created_by` é escolhido
entre os utilizadores ativos devolvidos pela API; não existe um ID de criador
fixo no frontend.

## Perfis e início de sessão

A aplicação tem dois perfis: o **Administrador** acede às áreas administrativa
e de trabalho; o **Utilizador** acede apenas ao front-office e só pode consultar
e atualizar o estado das tarefas que lhe foram atribuídas. As contas são
criadas por um administrador, que também pode alterar o perfil na página de
utilizadores.

O login guarda o token apenas na sessão atual do navegador. O middleware
redireciona cada perfil para a área permitida, mas a autorização efetiva é
sempre validada pela API. A primeira conta de administrador é configurada no
backend; consulte as instruções de autenticação no README do backend.

No código, `carregarArea` obtém membros e projetos, `carregarTarefas` pede as
tarefas do utilizador autenticado e `alterarEstado` atualiza o estado via
`PATCH`. As conversões e os cálculos de resumo estão na própria página para
manter o fluxo da interface explícito.

## Quadro Kanban

A página `/tasks` organiza as tarefas em quatro colunas por estado. É possível
arrastar cartões entre colunas para persistir uma mudança de estado na API; o
clique num cartão abre os detalhes, onde é possível alterar o estado, editar ou
eliminar a tarefa. Os cartões mostram apenas a categoria, o identificador, o
título e a prioridade para manter o quadro compacto. A pesquisa e os filtros
continuam disponíveis, e as tarefas de projetos arquivados não podem ser
alteradas nem eliminadas.

Para persistir alterações, mantém o backend ativo no endereço configurado em
`NUXT_PUBLIC_API_BASE`. A lista de responsáveis inclui apenas membros ativos
do projeto; adiciona primeiro o utilizador em **Projetos → Membros**.

Look at the [Nuxt documentation](https://nuxt.com/docs/getting-started/introduction) to learn more.

## Setup

Make sure to install dependencies:

```bash
# npm
npm install

# pnpm
pnpm install

# yarn
yarn install

# bun
bun install
```

## Development Server

Start the development server on `http://localhost:3000`:

```bash
# npm
npm run dev

# pnpm
pnpm dev

# yarn
yarn dev

# bun
bun run dev
```

## Production

Build the application for production:

```bash
# npm
npm run build

# pnpm
pnpm build

# yarn
yarn build

# bun
bun run build
```

Locally preview production build:

```bash
# npm
npm run preview

# pnpm
pnpm preview

# yarn
yarn preview

# bun
bun run preview
```

Check out the [deployment documentation](https://nuxt.com/docs/getting-started/deployment) for more information.
