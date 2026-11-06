# Nuxt Minimal Starter

The frontend communicates with the TaskFlow FastAPI backend. By default, it
uses `http://127.0.0.1:8000` for local development; set `NUXT_PUBLIC_API_BASE`
if the backend is at another address. PostgreSQL credentials belong only in
the backend environment; do not put them in Nuxt runtime configuration.

## Área de trabalho (front-office)

O caminho `/my-work` reúne o painel do front-office e a área operacional:
indicadores, prazos e riscos dos projetos acessíveis, além de tarefas
atribuídas, pesquisa/filtros, registos de trabalho e anexos. `/front-office`
redireciona para esta página unificada.
As páginas `/projects` e `/tasks` disponibilizam também o espaço colaborativo
para gerir projetos e tarefas conforme o papel de cada utilizador.

O front-office utiliza a sessão autenticada para identificar o membro e mostrar
apenas o seu trabalho.

O caminho `/calendar` apresenta os prazos das tarefas dos projetos acessíveis
ao utilizador, com navegação mensal, filtro por projeto e agenda do dia
selecionado, com vistas de mês, semana e dia, filtros e resumo de conclusão.
Eventos podem ser criados como pessoais ou partilhados com um projeto. Os
administradores veem os eventos da plataforma; os restantes perfis veem os
seus eventos pessoais e os eventos dos projetos a que pertencem. A criação de
eventos partilhados exige o papel de responsável ou colaborador. Aplique
`20261102_0006` no backend antes de usar a gestão de eventos.

## Equipas

O caminho `/teams` permite consultar equipas, adicionar ou remover utilizadores,
editar os dados da equipa e associar projetos. Administradores e responsáveis
de projetos podem gerir equipas. A associação não altera automaticamente os
membros nem as permissões de cada projeto. Aplique a migração `20261102_0007`
no backend antes de usar esta funcionalidade.

Os IDs de utilizadores, projetos e tarefas são gerados pelo PostgreSQL
(`Identity`). Projetos e tarefas ficam associados à conta autenticada que os
criou; não existe um ID de criador fixo no frontend.

## Perfis e início de sessão

A aplicação tem os perfis globais **Administrador** e **Utilizador**. Qualquer
utilizador autenticado pode criar projetos e torna-se o seu responsável. Os
papéis por projeto são **Responsável** (gerir o projeto e a equipa),
**Colaborador** (criar, atualizar e documentar tarefas) e **Observador**
(consultar tarefas e histórico). Contas continuam a ser criadas por um
administrador; este também pode gerir a plataforma.

O login guarda os tokens apenas na sessão atual do navegador. É possível
adicionar outra conta e alternar entre as contas autenticadas no cabeçalho; a
sessão atual mantém-se se o novo login falhar. **Terminar sessão** remove os
tokens guardados nesta sessão do navegador. O middleware redireciona cada perfil
para a área permitida, mas a autorização efetiva é sempre validada pela API. A
primeira conta de administrador é configurada no backend; consulte as instruções
de autenticação no README do backend.

### Separação entre áreas e permissões

O TaskFlow mantém **as mesmas páginas operacionais** para evitar duplicação de
informação e fluxos diferentes. A apresentação e as ações disponíveis são
adaptadas ao papel autenticado:

| Área/página | Administrador (back-office) | Utilizador (front-office) |
| --- | --- | --- |
| `/` Dashboard, `/users`, `/reports` | Acesso total | Sem acesso; redirecionado para `/my-work` |
| `/projects`, `/tasks`, `/calendar`, `/teams` | Acesso transversal e gestão global | Apenas projetos/equipas a que pertence; ações dependem do papel no projeto |
| `/my-work`, `/settings` | Disponíveis no shell comum | Disponíveis no shell comum |

Dentro de um projeto, o backend continua a aplicar as permissões em cada
pedido: **Responsável** gere projeto, membros e tarefas; **Colaborador** cria,
atualiza e documenta tarefas; **Observador** apenas consulta. Ocultar uma ação
no frontend melhora a experiência, mas não substitui a validação da API.

Na lista de **Utilizadores**, selecionar um nome abre a página `/users/:id`,
com o perfil, as tarefas atribuídas e as equipas desse utilizador. O endereço
direto do perfil também pode ser aberto ou partilhado por administradores.

No código, `carregarArea` obtém membros e projetos, `carregarTarefas` pede as
tarefas do utilizador autenticado e `alterarEstado` atualiza o estado via
`PATCH`. As conversões e os cálculos de resumo estão na própria página para
manter o fluxo da interface explícito.

## Quadro Kanban

A página `/tasks` organiza as tarefas dos projetos acessíveis em quatro colunas
por estado. Responsáveis e colaboradores podem criar e atualizar tarefas; só
responsáveis podem eliminá-las. Observadores têm acesso de consulta. O clique
num cartão abre os detalhes e as tarefas de projetos arquivados não podem ser
alteradas.

Cada tarefa tem um responsável, selecionado pelo administrador ou pelo
responsável do projeto entre os membros ativos não observadores. As migrações
`20261106_0008` e `20261106_0009` criam a associação, preservam o responsável
principal existente e impõem o limite de um responsável por tarefa.

Para persistir alterações, mantém o backend ativo no endereço configurado em
`NUXT_PUBLIC_API_BASE`. A lista de responsáveis inclui apenas membros ativos
do projeto; adiciona primeiro o utilizador em **Projetos → Membros**.
Em **Projetos → Membros**, o responsável vê e seleciona contas ativas já
registadas que ainda não pertencem ao projeto. Uma conta inexistente não é
criada automaticamente: um administrador tem de a registar primeiro em
**Utilizadores**.

## Radar de risco

Os dashboards administrativo e do front-office incluem um Radar de risco para
projetos ativos. O Radar assinala tarefas bloqueadas, tarefas não concluídas
com prazo ultrapassado e projetos sem atualizações registadas há pelo menos
sete dias. A atividade considera a criação/atualização do projeto e das tarefas;
registos de trabalho também atualizam a data da tarefa. No front-office, a API
limita os riscos aos projetos a que o utilizador tem acesso.

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
