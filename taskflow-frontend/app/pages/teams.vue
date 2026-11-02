<script setup lang="ts">
definePageMeta({ layout: 'admin' })

interface ProjetoAPI {
  id: number
  name: string
  status: 'active' | 'completed' | 'archived'
  team_id: number | null
  current_user_role: 'admin' | 'owner' | 'contributor' | 'viewer'
}

interface ProjetoEquipa {
  id: number
  name: string
  status: string
}

interface EquipaAPI {
  id: number
  name: string
  description: string | null
  created_by: number
  created_at: string
  updated_at: string
  member_count: number
  projects: ProjetoEquipa[]
  can_manage: boolean
  can_associate_projects: boolean
}

interface MembroEquipa {
  user_id: number
  name: string
  email: string
  avatar_url: string | null
}

const api = useNuxtApp().$api
const auth = useAuth()
const equipas = ref<EquipaAPI[]>([])
const projetos = ref<ProjetoAPI[]>([])
const membros = ref<MembroEquipa[]>([])
const utilizadoresDisponiveis = ref<MembroEquipa[]>([])
const carregando = ref(true)
const erro = ref('')
const erroDetalhe = ref('')
const sucesso = ref('')
const pesquisa = ref('')
const modalFormulario = ref(false)
const modalDetalhe = ref(false)
const equipaSelecionada = ref<EquipaAPI | null>(null)
const editarEquipa = ref(false)
const aGuardar = ref(false)
const aAdicionarMembro = ref(false)
const membroEmRemocao = ref<number | null>(null)
const projetoEmAtualizacao = ref<number | null>(null)
const utilizadoresSelecionados = ref<number[]>([])
const pesquisarUtilizadores = ref('')
const projetoSelecionado = ref('')
const formulario = ref({ name: '', description: '' })

const podeCriarEquipa = computed(() =>
  auth.user.value?.role === 'admin' ||
  projetos.value.some(projeto => projeto.current_user_role === 'owner'),
)

const equipasFiltradas = computed(() => {
  const termo = pesquisa.value.trim().toLocaleLowerCase('pt-PT')
  if (!termo) return equipas.value
  return equipas.value.filter(equipa =>
    `${equipa.name} ${equipa.description ?? ''} ${equipa.projects.map(project => project.name).join(' ')}`
      .toLocaleLowerCase('pt-PT')
      .includes(termo),
  )
})

const projetosDisponiveis = computed(() =>
  projetos.value.filter(projeto =>
    equipaSelecionada.value &&
    (projeto.current_user_role === 'admin' || projeto.current_user_role === 'owner') &&
    (projeto.team_id === null || projeto.team_id === equipaSelecionada.value.id),
  ),
)

const utilizadoresFiltrados = computed(() => {
  const termo = pesquisarUtilizadores.value.trim().toLocaleLowerCase('pt-PT')
  if (!termo) return utilizadoresDisponiveis.value
  return utilizadoresDisponiveis.value.filter(user =>
    `${user.name} ${user.email}`.toLocaleLowerCase('pt-PT').includes(termo),
  )
})

async function carregarDados(): Promise<void> {
  carregando.value = true
  erro.value = ''
  try {
    const [equipasAPI, projetosAPI] = await Promise.all([
      api<EquipaAPI[]>('/teams/'),
      api<ProjetoAPI[]>('/projects/'),
    ])
    equipas.value = equipasAPI
    projetos.value = projetosAPI
  } catch (error) {
    console.error('Erro ao carregar equipas:', error)
    erro.value = mensagemErro(error)
  } finally {
    carregando.value = false
  }
}

function abrirCriacao(): void {
  formulario.value = { name: '', description: '' }
  erro.value = ''
  modalFormulario.value = true
}

async function guardarEquipa(): Promise<void> {
  const name = formulario.value.name.trim()
  if (!name) {
    erro.value = 'O nome da equipa é obrigatório.'
    return
  }

  aGuardar.value = true
  erro.value = ''
  try {
    const criada = await api<EquipaAPI>('/teams/', {
      method: 'POST',
      body: {
        name,
        description: formulario.value.description.trim() || null,
      },
    })
    equipas.value.push(criada)
    modalFormulario.value = false
    await abrirDetalhe(criada)
    sucesso.value = 'Equipa criada com sucesso.'
  } catch (error) {
    console.error('Erro ao criar equipa:', error)
    erro.value = mensagemErro(error)
  } finally {
    aGuardar.value = false
  }
}

async function abrirDetalhe(equipa: EquipaAPI): Promise<void> {
  equipaSelecionada.value = equipa
  membros.value = []
  utilizadoresDisponiveis.value = []
  erroDetalhe.value = ''
  sucesso.value = ''
  editarEquipa.value = false
  utilizadoresSelecionados.value = []
  pesquisarUtilizadores.value = ''
  projetoSelecionado.value = ''
  modalDetalhe.value = true
  try {
    const [equipaAtualizada, membrosAPI] = await Promise.all([
      api<EquipaAPI>(`/teams/${equipa.id}`),
      api<MembroEquipa[]>(`/teams/${equipa.id}/members`),
    ])
    atualizarEquipaLocal(equipaAtualizada)
    equipaSelecionada.value = equipaAtualizada
    membros.value = membrosAPI
    if (equipaAtualizada.can_manage) {
      utilizadoresDisponiveis.value = await api<MembroEquipa[]>(
        `/teams/${equipa.id}/available-members`,
      )
    }
  } catch (error) {
    console.error('Erro ao abrir equipa:', error)
    erroDetalhe.value = mensagemErro(error)
  }
}

function atualizarEquipaLocal(atualizada: EquipaAPI): void {
  const indice = equipas.value.findIndex(equipa => equipa.id === atualizada.id)
  if (indice === -1) equipas.value.push(atualizada)
  else equipas.value[indice] = atualizada
}

async function guardarEdicao(): Promise<void> {
  if (!equipaSelecionada.value) return
  const name = equipaSelecionada.value.name.trim()
  if (!name) {
    erroDetalhe.value = 'O nome da equipa é obrigatório.'
    return
  }

  aGuardar.value = true
  erroDetalhe.value = ''
  try {
    const atualizada = await api<EquipaAPI>(`/teams/${equipaSelecionada.value.id}`, {
      method: 'PATCH',
      body: {
        name,
        description: equipaSelecionada.value.description?.trim() || null,
      },
    })
    equipaSelecionada.value = atualizada
    atualizarEquipaLocal(atualizada)
    editarEquipa.value = false
    sucesso.value = 'Dados da equipa atualizados.'
  } catch (error) {
    console.error('Erro ao atualizar equipa:', error)
    erroDetalhe.value = mensagemErro(error)
  } finally {
    aGuardar.value = false
  }
}

async function eliminarEquipa(): Promise<void> {
  if (!equipaSelecionada.value) return
  if (!window.confirm(`Eliminar a equipa "${equipaSelecionada.value.name}"? Os projetos associados serão mantidos.`)) return

  aGuardar.value = true
  erroDetalhe.value = ''
  try {
    await api(`/teams/${equipaSelecionada.value.id}`, { method: 'DELETE' })
    equipas.value = equipas.value.filter(equipa => equipa.id !== equipaSelecionada.value?.id)
    projetos.value = projetos.value.map(projeto =>
      projeto.team_id === equipaSelecionada.value?.id
        ? { ...projeto, team_id: null }
        : projeto,
    )
    modalDetalhe.value = false
    equipaSelecionada.value = null
    sucesso.value = 'Equipa eliminada. Os projetos foram mantidos.'
  } catch (error) {
    console.error('Erro ao eliminar equipa:', error)
    erroDetalhe.value = mensagemErro(error)
  } finally {
    aGuardar.value = false
  }
}

async function adicionarMembro(): Promise<void> {
  if (!equipaSelecionada.value || !utilizadoresSelecionados.value.length) return
  aAdicionarMembro.value = true
  erroDetalhe.value = ''
  try {
    const novosMembros = await api<MembroEquipa[]>(
      `/teams/${equipaSelecionada.value.id}/members/bulk`,
      {
        method: 'POST',
        body: { user_ids: utilizadoresSelecionados.value },
      },
    )
    membros.value.push(...novosMembros)
    utilizadoresDisponiveis.value = utilizadoresDisponiveis.value.filter(
      utilizador => !utilizadoresSelecionados.value.includes(utilizador.user_id),
    )
    utilizadoresSelecionados.value = []
    await atualizarResumoEquipa()
  } catch (error) {
    console.error('Erro ao adicionar membro à equipa:', error)
    erroDetalhe.value = mensagemErro(error)
  } finally {
    aAdicionarMembro.value = false
  }
}

function selecionarTodosUtilizadores(selecionar: boolean): void {
  const idsVisiveis = utilizadoresFiltrados.value.map(user => user.user_id)
  if (selecionar) {
    utilizadoresSelecionados.value = [
      ...new Set([...utilizadoresSelecionados.value, ...idsVisiveis]),
    ]
  } else {
    utilizadoresSelecionados.value = utilizadoresSelecionados.value.filter(
      id => !idsVisiveis.includes(id),
    )
  }
}

async function removerMembro(membro: MembroEquipa): Promise<void> {
  if (!equipaSelecionada.value) return
  if (!window.confirm(`Remover ${membro.name} desta equipa?`)) return
  membroEmRemocao.value = membro.user_id
  erroDetalhe.value = ''
  try {
    await api(
      `/teams/${equipaSelecionada.value.id}/members/${membro.user_id}`,
      { method: 'DELETE' },
    )
    membros.value = membros.value.filter(item => item.user_id !== membro.user_id)
    utilizadoresDisponiveis.value.push(membro)
    await atualizarResumoEquipa()
  } catch (error) {
    console.error('Erro ao remover membro da equipa:', error)
    erroDetalhe.value = mensagemErro(error)
  } finally {
    membroEmRemocao.value = null
  }
}

async function atualizarAssociacaoProjeto(project: ProjetoAPI, associar: boolean): Promise<void> {
  if (!equipaSelecionada.value) return
  projetoEmAtualizacao.value = project.id
  erroDetalhe.value = ''
  try {
    const url = `/teams/${equipaSelecionada.value.id}/projects/${project.id}`
    const atualizada = associar
      ? await api<EquipaAPI>(url, { method: 'POST' })
      : await api<EquipaAPI>(url, { method: 'DELETE' })
    equipaSelecionada.value = atualizada
    atualizarEquipaLocal(atualizada)
    projetos.value = projetos.value.map(item =>
      item.id === project.id
        ? { ...item, team_id: associar ? atualizada.id : null }
        : item,
    )
    projetoSelecionado.value = ''
  } catch (error) {
    console.error('Erro ao atualizar associação do projeto:', error)
    erroDetalhe.value = mensagemErro(error)
  } finally {
    projetoEmAtualizacao.value = null
  }
}

async function associarProjetoSelecionado(): Promise<void> {
  const project = projetosDisponiveis.value.find(
    item => String(item.id) === projetoSelecionado.value && item.team_id === null,
  )
  if (project) await atualizarAssociacaoProjeto(project, true)
}

async function desassociarProjeto(projectId: number): Promise<void> {
  const project = projetos.value.find(item => item.id === projectId)
  if (project) await atualizarAssociacaoProjeto(project, false)
}

async function atualizarResumoEquipa(): Promise<void> {
  if (!equipaSelecionada.value) return
  const atualizada = await api<EquipaAPI>(`/teams/${equipaSelecionada.value.id}`)
  equipaSelecionada.value = atualizada
  atualizarEquipaLocal(atualizada)
}

function fecharDetalhe(): void {
  if (aGuardar.value || aAdicionarMembro.value || membroEmRemocao.value !== null || projetoEmAtualizacao.value !== null) return
  modalDetalhe.value = false
  equipaSelecionada.value = null
  erroDetalhe.value = ''
}

function mensagemErro(error: unknown): string {
  if (typeof error === 'object' && error !== null && 'data' in error) {
    const data = error.data
    if (typeof data === 'object' && data !== null && 'detail' in data && typeof data.detail === 'string') {
      return data.detail
    }
  }
  return 'Não foi possível concluir a operação. Verifique a ligação à API e tente novamente.'
}

onMounted(carregarDados)
</script>

<template>
  <section class="teams-page">
    <header class="page-heading">
      <div>
        <span class="eyebrow">ESPAÇO DE TRABALHO</span>
        <h1>Equipas</h1>
        <p>Organize pessoas e associe projetos a equipas de trabalho.</p>
      </div>
      <button v-if="podeCriarEquipa" class="primary-button" type="button" @click="abrirCriacao">
        <span aria-hidden="true">＋</span> Criar equipa
      </button>
    </header>

    <p v-if="erro" class="notice notice-error" role="alert">{{ erro }}</p>
    <p v-if="sucesso" class="notice notice-success" role="status">{{ sucesso }}</p>

    <div class="toolbar">
      <label class="search-field">
        <span aria-hidden="true">⌕</span>
        <input v-model="pesquisa" type="search" placeholder="Pesquisar equipas ou projetos">
      </label>
      <span class="team-count">{{ equipasFiltradas.length }} equipa(s)</span>
    </div>

    <div v-if="carregando" class="empty-state">A carregar equipas…</div>
    <div v-else-if="!equipas.length" class="empty-state">
      <span class="empty-icon" aria-hidden="true">♙</span>
      <h2>Ainda não existem equipas visíveis</h2>
      <p v-if="podeCriarEquipa">Crie uma equipa para reunir membros e organizar projetos.</p>
      <p v-else>As equipas a que pertence ou que estão associadas aos seus projetos aparecerão aqui.</p>
      <button v-if="podeCriarEquipa" class="primary-button" type="button" @click="abrirCriacao">Criar primeira equipa</button>
    </div>
    <div v-else-if="!equipasFiltradas.length" class="empty-state">
      Não foram encontradas equipas para esta pesquisa.
    </div>
    <div v-else class="team-grid">
      <article v-for="equipa in equipasFiltradas" :key="equipa.id" class="team-card">
        <div class="card-top">
          <div class="team-mark" aria-hidden="true">{{ equipa.name.slice(0, 1).toUpperCase() }}</div>
          <span v-if="equipa.can_manage" class="manager-badge">Gestor</span>
        </div>
        <h2>{{ equipa.name }}</h2>
        <p class="team-description">{{ equipa.description || 'Sem descrição.' }}</p>
        <div class="team-stats">
          <span><strong>{{ equipa.member_count }}</strong> membros</span>
          <span><strong>{{ equipa.projects.length }}</strong> projetos</span>
        </div>
        <div class="project-tags">
          <span v-for="project in equipa.projects.slice(0, 3)" :key="project.id">{{ project.name }}</span>
          <span v-if="equipa.projects.length > 3" class="more-tag">+{{ equipa.projects.length - 3 }}</span>
          <span v-if="!equipa.projects.length" class="muted-tag">Sem projetos associados</span>
        </div>
        <button class="card-action" type="button" @click="abrirDetalhe(equipa)">
          Ver equipa <span aria-hidden="true">→</span>
        </button>
      </article>
    </div>

    <div v-if="modalFormulario" class="modal-backdrop" @click.self="modalFormulario = false">
      <section class="team-modal create-modal" role="dialog" aria-modal="true" aria-labelledby="create-team-title">
        <header class="modal-heading">
          <div><span class="eyebrow">NOVA EQUIPA</span><h2 id="create-team-title">Criar equipa</h2></div>
          <button type="button" aria-label="Fechar" :disabled="aGuardar" @click="modalFormulario = false">×</button>
        </header>
        <form class="team-form" @submit.prevent="guardarEquipa">
          <label>Nome da equipa<input v-model="formulario.name" maxlength="255" required placeholder="Ex.: Desenvolvimento"></label>
          <label>Descrição<textarea v-model="formulario.description" rows="3" maxlength="5000" placeholder="Objetivos e área de atuação"></textarea></label>
          <p v-if="erro" class="form-error" role="alert">{{ erro }}</p>
          <footer class="modal-actions">
            <button class="secondary-button" type="button" :disabled="aGuardar" @click="modalFormulario = false">Cancelar</button>
            <button class="primary-button" type="submit" :disabled="aGuardar">{{ aGuardar ? 'A criar…' : 'Criar equipa' }}</button>
          </footer>
        </form>
      </section>
    </div>

    <div v-if="modalDetalhe && equipaSelecionada" class="modal-backdrop" @click.self="fecharDetalhe">
      <section class="team-modal detail-modal" role="dialog" aria-modal="true" aria-labelledby="team-detail-title">
        <header class="modal-heading">
          <div>
            <span class="eyebrow">EQUIPA · {{ membros.length }} MEMBRO(S)</span>
            <h2 id="team-detail-title">{{ equipaSelecionada.name }}</h2>
          </div>
          <button type="button" aria-label="Fechar" @click="fecharDetalhe">×</button>
        </header>

        <p v-if="erroDetalhe" class="form-error" role="alert">{{ erroDetalhe }}</p>
        <p v-if="sucesso" class="notice notice-success" role="status">{{ sucesso }}</p>

        <form v-if="editarEquipa && equipaSelecionada.can_manage" class="team-form edit-form" @submit.prevent="guardarEdicao">
          <label>Nome da equipa<input v-model="equipaSelecionada.name" maxlength="255" required></label>
          <label>Descrição<textarea v-model="equipaSelecionada.description" rows="3" maxlength="5000"></textarea></label>
          <div class="inline-actions">
            <button class="secondary-button" type="button" @click="editarEquipa = false">Cancelar</button>
            <button class="primary-button" type="submit" :disabled="aGuardar">{{ aGuardar ? 'A guardar…' : 'Guardar alterações' }}</button>
          </div>
        </form>
        <div v-else class="team-summary">
          <p>{{ equipaSelecionada.description || 'Sem descrição.' }}</p>
          <button v-if="equipaSelecionada.can_manage" class="text-button" type="button" @click="editarEquipa = true">Editar dados da equipa</button>
        </div>

        <section class="detail-section">
          <div class="section-heading">
            <div><h3>Membros</h3><span>{{ membros.length }} pessoa(s) na equipa</span></div>
          </div>
          <form v-if="equipaSelecionada.can_manage" class="member-selection" @submit.prevent="adicionarMembro">
            <label class="member-search">
              <span aria-hidden="true">⌕</span>
              <input v-model="pesquisarUtilizadores" type="search" placeholder="Pesquisar utilizadores ativos">
            </label>
            <div class="selection-toolbar">
              <span>{{ utilizadoresSelecionados.length }} selecionado(s)</span>
              <button type="button" @click="selecionarTodosUtilizadores(true)">Selecionar visíveis</button>
              <button type="button" @click="selecionarTodosUtilizadores(false)">Limpar seleção</button>
            </div>
            <div class="available-members" role="group" aria-label="Utilizadores disponíveis para a equipa">
              <label v-for="user in utilizadoresFiltrados" :key="user.user_id" class="available-member">
                <input v-model="utilizadoresSelecionados" type="checkbox" :value="user.user_id">
                <span class="member-avatar">{{ user.name.slice(0, 1).toUpperCase() }}</span>
                <span class="member-copy"><strong>{{ user.name }}</strong><small>{{ user.email }}</small></span>
              </label>
              <p v-if="!utilizadoresFiltrados.length" class="list-empty">
                {{ utilizadoresDisponiveis.length ? 'Nenhum utilizador corresponde à pesquisa.' : 'Não há mais utilizadores ativos disponíveis.' }}
              </p>
            </div>
            <button class="primary-button compact-button" type="submit" :disabled="!utilizadoresSelecionados.length || aAdicionarMembro">
              {{ aAdicionarMembro ? 'A adicionar…' : `Adicionar ${utilizadoresSelecionados.length || ''} membro(s)` }}
            </button>
          </form>
          <ul class="member-list">
            <li v-for="membro in membros" :key="membro.user_id">
              <span class="member-avatar">{{ membro.name.slice(0, 1).toUpperCase() }}</span>
              <span class="member-copy"><strong>{{ membro.name }}</strong><small>{{ membro.email }}</small></span>
              <button
                v-if="equipaSelecionada.can_manage"
                class="remove-button"
                type="button"
                :aria-label="`Remover ${membro.name}`"
                :disabled="membroEmRemocao === membro.user_id"
                @click="removerMembro(membro)"
              >
                {{ membroEmRemocao === membro.user_id ? '…' : 'Remover' }}
              </button>
            </li>
            <li v-if="!membros.length" class="list-empty">Ainda não foram adicionados membros.</li>
          </ul>
        </section>

        <section class="detail-section">
          <div class="section-heading">
            <div><h3>Projetos associados</h3><span>Um projeto só pode pertencer a uma equipa.</span></div>
          </div>
          <form v-if="equipaSelecionada.can_associate_projects && projetosDisponiveis.some(project => project.team_id === null)" class="add-row" @submit.prevent="associarProjetoSelecionado">
            <select v-model="projetoSelecionado" aria-label="Selecionar projeto para associar">
              <option value="">Selecionar projeto que gere</option>
              <option v-for="project in projetosDisponiveis.filter(item => item.team_id === null)" :key="project.id" :value="String(project.id)">
                {{ project.name }}
              </option>
            </select>
            <button class="primary-button compact-button" type="submit" :disabled="!projetoSelecionado || projetoEmAtualizacao !== null">Associar</button>
          </form>
          <ul class="project-list">
            <li v-for="project in equipaSelecionada.projects" :key="project.id">
              <span class="project-mark" aria-hidden="true">▤</span>
              <span class="project-copy"><strong>{{ project.name }}</strong><small>{{ project.status === 'active' ? 'Ativo' : project.status === 'completed' ? 'Concluído' : 'Arquivado' }}</small></span>
              <button
                v-if="projetos.some(item => item.id === project.id && (item.current_user_role === 'admin' || item.current_user_role === 'owner'))"
                class="remove-button"
                type="button"
                :disabled="projetoEmAtualizacao === project.id"
                @click="desassociarProjeto(project.id)"
              >
                {{ projetoEmAtualizacao === project.id ? '…' : 'Desassociar' }}
              </button>
            </li>
            <li v-if="!equipaSelecionada.projects.length" class="list-empty">Ainda não há projetos associados.</li>
          </ul>
          <p class="association-note">Associar uma equipa não adiciona automaticamente os seus membros aos projetos nem altera as permissões existentes.</p>
        </section>

        <footer v-if="equipaSelecionada.can_manage" class="detail-footer">
          <button class="danger-button" type="button" :disabled="aGuardar" @click="eliminarEquipa">Eliminar equipa</button>
          <button class="secondary-button" type="button" @click="fecharDetalhe">Fechar</button>
        </footer>
      </section>
    </div>
  </section>
</template>

<style scoped>
.teams-page { display: grid; gap: 20px; color: #172b4d; }
.page-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.eyebrow { color: #8d99ad; font-size: 9px; font-weight: 800; letter-spacing: .12em; }
.page-heading h1 { margin: 5px 0; color: #1c2a43; font-size: clamp(25px, 3vw, 32px); letter-spacing: -.045em; }
.page-heading p { margin: 0; color: #78869d; font-size: 12px; }
.primary-button, .secondary-button, .danger-button { display: inline-flex; min-height: 38px; align-items: center; justify-content: center; gap: 7px; padding: 0 14px; border-radius: 9px; font-size: 11px; font-weight: 700; cursor: pointer; transition: .18s ease; }
.primary-button { color: #fff; background: linear-gradient(110deg, #5675ed, #4856ce); border: 0; box-shadow: 0 5px 12px rgb(75 91 211 / 18%); }
.primary-button:hover:not(:disabled) { background: #3948c1; }
.secondary-button { color: #52617a; background: #fff; border: 1px solid #dfe5ef; }
.danger-button { color: #ad3b49; background: #fff4f5; border: 1px solid #f0d4d7; }
button:disabled { opacity: .55; cursor: not-allowed; }
.notice { padding: 10px 13px; margin: 0; border-radius: 8px; font-size: 11px; }
.notice-error, .form-error { color: #a53d47; background: #fff3f3; border: 1px solid #f4d5d8; }
.notice-success { color: #26734f; background: #effaf4; border: 1px solid #d3efdf; }
.toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.search-field { display: flex; width: min(390px, 100%); min-height: 40px; align-items: center; gap: 9px; padding: 0 12px; background: #fff; border: 1px solid #e4e9f2; border-radius: 9px; }
.search-field > span { color: #8190a8; font-size: 20px; }
.search-field input { width: 100%; color: #283a57; background: transparent; border: 0; outline: 0; font: inherit; font-size: 11px; }
.team-count { color: #8793a7; font-size: 10px; }
.team-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(245px, 1fr)); gap: 14px; }
.team-card { display: flex; min-width: 0; flex-direction: column; padding: 17px; background: #fff; border: 1px solid #e7ebf3; border-radius: 13px; box-shadow: 0 4px 14px rgb(31 48 78 / 3%); }
.card-top { display: flex; align-items: center; justify-content: space-between; }
.team-mark { display: grid; width: 42px; height: 42px; place-items: center; color: #535fd2; background: linear-gradient(145deg, #eef0ff, #e1e6ff); border-radius: 12px; font-size: 17px; font-weight: 800; }
.manager-badge { padding: 5px 8px; color: #36795b; background: #eaf8f0; border-radius: 20px; font-size: 9px; font-weight: 700; }
.team-card h2 { overflow: hidden; margin: 13px 0 5px; color: #273752; font-size: 15px; text-overflow: ellipsis; white-space: nowrap; }
.team-description { display: -webkit-box; min-height: 32px; overflow: hidden; margin: 0; color: #78869a; font-size: 10px; line-height: 1.55; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.team-stats { display: flex; gap: 15px; padding: 13px 0 11px; color: #8692a5; font-size: 9px; }
.team-stats strong { color: #3a4b67; font-size: 11px; }
.project-tags { display: flex; min-height: 27px; flex-wrap: wrap; gap: 5px; }
.project-tags > span { max-width: 145px; overflow: hidden; padding: 5px 7px; color: #5865bc; background: #f0f1ff; border-radius: 6px; font-size: 8px; text-overflow: ellipsis; white-space: nowrap; }
.project-tags > .more-tag { color: #657187; background: #f0f2f6; }
.project-tags > .muted-tag { color: #909bad; background: #f5f6f9; }
.card-action { display: flex; width: 100%; align-items: center; justify-content: space-between; padding: 13px 0 0; margin-top: 13px; color: #4c5ecb; background: transparent; border: 0; border-top: 1px solid #edf0f5; font: inherit; font-size: 10px; font-weight: 700; text-align: left; cursor: pointer; }
.card-action:hover { color: #2939ae; }
.empty-state { display: grid; min-height: 230px; justify-items: center; align-content: center; gap: 9px; padding: 22px; color: #8591a5; background: #fff; border: 1px dashed #dce3ee; border-radius: 12px; font-size: 11px; text-align: center; }
.empty-state h2 { margin: 4px 0 0; color: #34445f; font-size: 15px; }
.empty-state p { margin: 0 0 5px; }
.empty-icon { color: #6471db; font-size: 27px; }
.modal-backdrop { position: fixed; z-index: 100; inset: 0; display: grid; overflow-y: auto; place-items: center; padding: 20px; background: rgb(17 28 48 / 48%); backdrop-filter: blur(3px); }
.team-modal { width: min(540px, 100%); max-height: min(90vh, 850px); overflow-y: auto; padding: 22px; background: #fff; border: 1px solid #e8ecf3; border-radius: 15px; box-shadow: 0 24px 70px rgb(17 28 48 / 25%); }
.create-modal { width: min(460px, 100%); }
.detail-modal { width: min(620px, 100%); }
.modal-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 15px; padding-bottom: 15px; border-bottom: 1px solid #edf0f5; }
.modal-heading h2 { margin: 5px 0 0; color: #23334f; font-size: 19px; letter-spacing: -.03em; }
.modal-heading > button { display: grid; width: 30px; height: 30px; place-items: center; color: #78869a; background: #f4f6f9; border: 0; border-radius: 8px; font-size: 21px; cursor: pointer; }
.team-form { display: grid; gap: 13px; padding-top: 16px; }
.team-form label { display: grid; gap: 6px; color: #53627a; font-size: 10px; font-weight: 700; }
.team-form input, .team-form textarea, .add-row select { width: 100%; box-sizing: border-box; padding: 10px 11px; color: #293951; background: #fff; border: 1px solid #dfe5ef; border-radius: 8px; outline: none; font: inherit; font-size: 11px; }
.team-form textarea { resize: vertical; }
.team-form input:focus, .team-form textarea:focus, .add-row select:focus { border-color: #8390ec; box-shadow: 0 0 0 3px rgb(99 112 224 / 12%); }
.modal-actions, .detail-footer { display: flex; justify-content: flex-end; gap: 8px; padding-top: 6px; }
.form-error { padding: 9px 10px; margin: 12px 0 0; border-radius: 7px; font-size: 10px; }
.team-summary { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; padding: 13px 0; }
.team-summary p { margin: 0; color: #6f7d93; font-size: 11px; line-height: 1.55; white-space: pre-line; }
.text-button { flex: 0 0 auto; padding: 0; color: #5263cc; background: transparent; border: 0; font: inherit; font-size: 9px; font-weight: 700; cursor: pointer; }
.detail-section { padding: 14px 0; border-top: 1px solid #edf0f5; }
.section-heading { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.section-heading h3 { margin: 0 0 3px; color: #2e3e59; font-size: 12px; }
.section-heading span { color: #8a96a9; font-size: 9px; }
.add-row { display: flex; gap: 7px; margin: 9px 0; }
.member-selection { display: grid; gap: 8px; padding: 10px; margin: 9px 0; background: #f8f9fc; border: 1px solid #e8ecf3; border-radius: 9px; }
.member-search { display: flex; min-height: 34px; align-items: center; gap: 7px; padding: 0 9px; background: #fff; border: 1px solid #e1e6ef; border-radius: 7px; }
.member-search > span { color: #8190a8; font-size: 17px; }
.member-search input { width: 100%; color: #293951; border: 0; outline: 0; font: inherit; font-size: 10px; }
.selection-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; color: #8490a3; font-size: 9px; }
.selection-toolbar span { margin-right: auto; font-weight: 700; }
.selection-toolbar button { padding: 0; color: #5263cc; background: transparent; border: 0; font: inherit; font-size: 9px; cursor: pointer; }
.available-members { display: grid; max-height: 180px; gap: 2px; overflow-y: auto; padding: 3px; background: #fff; border: 1px solid #e8ecf3; border-radius: 7px; }
.available-member { display: flex; min-width: 0; align-items: center; gap: 8px; padding: 6px; border-radius: 6px; cursor: pointer; }
.available-member:hover { background: #f5f6ff; }
.available-member > input { width: 15px; height: 15px; flex: 0 0 15px; accent-color: #5365d5; }
.add-row select { min-width: 0; flex: 1; padding: 9px; }
.compact-button { min-height: 34px; padding: 0 10px; font-size: 9px; }
.member-list, .project-list { display: grid; gap: 4px; padding: 0; margin: 0; list-style: none; }
.member-list li, .project-list li { display: flex; min-width: 0; align-items: center; gap: 9px; padding: 8px 4px; }
.member-avatar, .project-mark { display: grid; width: 31px; height: 31px; flex: 0 0 31px; place-items: center; color: #5968ca; background: #eef0ff; border-radius: 50%; font-size: 11px; font-weight: 750; }
.project-mark { background: #edf5ff; border-radius: 9px; }
.member-copy, .project-copy { display: grid; min-width: 0; flex: 1; gap: 3px; }
.member-copy strong, .project-copy strong { overflow: hidden; color: #3a4a65; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.member-copy small, .project-copy small { overflow: hidden; color: #8b97a9; font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }
.remove-button { padding: 6px 8px; color: #a6535d; background: #fff8f8; border: 1px solid #f0e0e1; border-radius: 7px; font: inherit; font-size: 9px; cursor: pointer; }
.list-empty { color: #929daf; font-size: 10px; }
.association-note { padding: 8px 9px; margin: 10px 0 0; color: #75839a; background: #f6f8fc; border-radius: 7px; font-size: 9px; line-height: 1.5; }
.detail-footer { justify-content: space-between; padding-top: 14px; margin-top: 4px; border-top: 1px solid #edf0f5; }
.inline-actions { display: flex; justify-content: flex-end; gap: 8px; }

@media (max-width: 600px) {
  .page-heading { align-items: flex-start; }
  .page-heading .primary-button { flex: 0 0 auto; min-height: 34px; padding: 0 9px; font-size: 9px; }
  .team-grid { grid-template-columns: 1fr; }
  .team-summary { flex-direction: column; }
  .team-modal { padding: 16px; }
  .add-row { align-items: stretch; }
  .remove-button { padding: 5px; }
}
</style>
