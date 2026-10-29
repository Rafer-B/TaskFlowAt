
<!--<script setup lang="ts">
definePageMeta({
  layout: 'admin',
})
import { computed, ref } from 'vue'

interface Projeto {
  id: number
  name: string
  description: string
  status: 'Ativo' | 'Concluído' | 'Arquivado'
  createdAt: string
}

const projetos = ref<Projeto[]>([
  {
    id: 1,
    name: 'Desenvolvimento do TaskFlow',
    description: 'Plataforma de gestão e colaboração em projetos académicos.',
    status: 'Ativo',
    createdAt: '2026-10-20'
  },
  {
    id: 2,
    name: 'Projeto de Bases de Dados',
    description: 'Modelação e implementação de uma base de dados PostgreSQL.',
    status: 'Ativo',
    createdAt: '2026-10-18'
  },
  {
    id: 3,
    name: 'Trabalho de Segurança',
    description: 'Pesquisa sobre ferramentas de segurança de redes.',
    status: 'Concluído',
    createdAt: '2026-10-10'
  }
])

const pesquisa = ref('')
const mostrarFormulario = ref(false)
const erro = ref('')

const novoProjeto = ref({
  name: '',
  description: ''
})

const projetosFiltrados = computed(() => {
  const termo = pesquisa.value.trim().toLowerCase()

  if (!termo) return projetos.value

  return projetos.value.filter((projeto) =>
    `${projeto.name} ${projeto.description}`
      .toLowerCase()
      .includes(termo)
  )
})

function adicionarProjeto() {
  erro.value = ''

  const nome = novoProjeto.value.name.trim()
  const descricao = novoProjeto.value.description.trim()

  if (!nome) {
    erro.value = 'O nome do projeto é obrigatório.'
    return
  }

  const projeto: Projeto = {
    id: Date.now(),
    name: nome,
    description: descricao,
    status: 'Ativo',
    createdAt: new Date().toISOString().slice(0, 10)
  }

  projetos.value.unshift(projeto)

  novoProjeto.value = {
    name: '',
    description: ''
  }

  mostrarFormulario.value = false
}
</script>-->

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

definePageMeta({
  layout: 'admin',
})

interface ProjetoAPI {
  id: number
  name: string
  description: string | null
  status: 'active' | 'completed' | 'archived'
  created_by: number
  created_at: string
  updated_at: string
  archived_at: string | null
}

type EstadoProjeto = 'Ativo' | 'Concluído' | 'Arquivado'

interface Projeto {
  id: number
  name: string
  description: string
  status: EstadoProjeto
  createdAt: string
}

const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const projetos = ref<Projeto[]>([])
const pesquisa = ref('')
const mostrarFormulario = ref(false)
const erro = ref('')
const carregando = ref(false)
const aGuardar = ref(false)

// Temporário: substitui pelo ID real de um utilizador existente.
const utilizadorId = 1

const novoProjeto = ref({
  name: '',
  description: '',
})

function converterEstado(estado: ProjetoAPI['status']): EstadoProjeto {
  const estados: Record<ProjetoAPI['status'], EstadoProjeto> = {
    active: 'Ativo',
    completed: 'Concluído',
    archived: 'Arquivado',
  }

  return estados[estado]
}

function converterProjeto(projeto: ProjetoAPI): Projeto {
  return {
    id: projeto.id,
    name: projeto.name,
    description: projeto.description ?? '',
    status: converterEstado(projeto.status),
    createdAt: projeto.created_at.slice(0, 10),
  }
}

const projetosFiltrados = computed(() => {
  const termo = pesquisa.value.trim().toLowerCase()

  if (!termo) return projetos.value

  return projetos.value.filter((projeto) =>
    `${projeto.name} ${projeto.description}`
      .toLowerCase()
      .includes(termo),
  )
})

async function carregarProjetos() {
  erro.value = ''
  carregando.value = true

  try {
    const resposta = await $fetch<ProjetoAPI[]>(`${apiBase}/projects/`)
    projetos.value = resposta.map(converterProjeto)
  } catch (error) {
    console.error('Erro ao carregar projetos:', error)
    erro.value = 'Não foi possível carregar os projetos. Confirma se a API está ativa.'
  } finally {
    carregando.value = false
  }
}

async function adicionarProjeto() {
  erro.value = ''

  const name = novoProjeto.value.name.trim()
  const description = novoProjeto.value.description.trim()

  if (!name) {
    erro.value = 'O nome do projeto é obrigatório.'
    return
  }

  aGuardar.value = true

  try {
    const criado = await $fetch<ProjetoAPI>(`${apiBase}/projects/`, {
      method: 'POST',
      body: {
        name,
        description: description || null,
        created_by: utilizadorId,
      },
    })

    projetos.value.unshift(converterProjeto(criado))

    novoProjeto.value = {
      name: '',
      description: '',
    }

    mostrarFormulario.value = false
  } catch (error) {
    console.error('Erro ao criar projeto:', error)
    erro.value =
      'Não foi possível guardar o projeto. Confirma se o utilizador existe e se a API está disponível.'
  } finally {
    aGuardar.value = false
  }
}

onMounted(carregarProjetos)
</script>

<template>
  <main class="page">
    <header class="page-header">
      <div>
        <NuxtLink to="/" class="back-link">
          ← Voltar ao painel
        </NuxtLink>

        <h1>Projetos</h1>
        <p>Organiza os teus projetos académicos num único lugar.</p>
      </div>

      <button
        class="primary-button"
        @click="mostrarFormulario = !mostrarFormulario"
      >
        {{ mostrarFormulario ? 'Cancelar' : '+ Novo projeto' }}
      </button>
    </header>

    <section v-if="mostrarFormulario" class="form-card">
      <h2>Criar projeto</h2>

      <form @submit.prevent="adicionarProjeto">
        <label for="nome">Nome do projeto</label>
        <input
          id="nome"
          v-model="novoProjeto.name"
          type="text"
          placeholder="Ex.: Trabalho de Engenharia de Software"
          maxlength="150"
          required
        />

        <label for="descricao">Descrição</label>
        
        <textarea
          id="descricao"
          v-model="novoProjeto.description"
          placeholder="Descreve brevemente o projeto..."
          rows="3"
          maxlength="2000"
        ></textarea>


        <p v-if="erro" class="error-message">
          {{ erro }}
        </p>

        
    <button type="submit" class="primary-button" :disabled="aGuardar">
      {{ aGuardar ? 'A guardar...' : 'Guardar projeto' }}
    </button>

      </form>
    </section>
    
    <p v-if="carregando" class="empty-state">
      A carregar projetos...
    </p>

    <p v-if="erro" class="error-message" role="alert">
      {{ erro }}
    </p>

    <section class="projects-section">
      <div class="list-toolbar">
        <h2>Os meus projetos</h2>

        <input
          v-model="pesquisa"
          class="search-input"
          type="search"
          placeholder="Pesquisar projetos..."
          aria-label="Pesquisar projetos"
        />
      </div>

      <p v-if="projetosFiltrados.length === 0" class="empty-state">
        Não foram encontrados projetos.
      </p>

      <div v-else class="projects-grid">
        <article
          v-for="projeto in projetosFiltrados"
          :key="projeto.id"
          class="project-card"
        >
          <div class="project-card-top">
            <span
              class="status"
              :class="projeto.status.toLowerCase()"
            >
              {{ projeto.status }}
            </span>
          </div>

          <h3>{{ projeto.name }}</h3>
          <p class="description">
            {{ projeto.description || 'Sem descrição.' }}
          </p>

          <div class="project-footer">
            <span>
              Criado em {{ projeto.createdAt }}
            </span>
            <NuxtLink
              :to="`/tasks?project=${projeto.id}`"
              class="text-link"
            >
              Ver tarefas →
            </NuxtLink>
          </div>
        </article>
      </div>
    </section>
  </main>
</template>

<style scoped>
.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 36px 24px;
  color: #172033;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 32px;
}

.back-link,
.text-link {
  color: #4f46e5;
  text-decoration: none;
  font-size: 14px;
}

.page-header h1 {
  margin: 14px 0 6px;
  font-size: 32px;
}

.page-header p {
  margin: 0;
  color: #64748b;
}

.primary-button {
  border: 0;
  border-radius: 8px;
  background: #4f46e5;
  color: white;
  padding: 12px 18px;
  font-weight: 600;
  cursor: pointer;
}

.primary-button:hover {
  background: #4338ca;
}

.form-card,
.project-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 22px;
}

.form-card {
  margin-bottom: 30px;
  max-width: 650px;
}

.form-card h2,
.list-toolbar h2 {
  margin-top: 0;
  font-size: 20px;
}

.form-card form {
  display: grid;
  gap: 10px;
}

.form-card input,
.form-card textarea,
.search-input {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 11px 12px;
  font: inherit;
}

.form-card label {
  margin-top: 8px;
  font-size: 14px;
  font-weight: 600;
}

.form-card textarea {
  resize: vertical;
}

.error-message {
  color: #b91c1c;
  margin: 4px 0;
}

.projects-section {
  margin-top: 24px;
}

.list-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.list-toolbar h2 {
  margin-bottom: 0;
}

.search-input {
  max-width: 300px;
  background: white;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
}

.project-card h3 {
  margin: 18px 0 10px;
  font-size: 18px;
}

.description {
  color: #64748b;
  line-height: 1.6;
  min-height: 48px;
}

.status {
  display: inline-block;
  border-radius: 20px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 600;
}

.status.ativo {
  color: #166534;
  background: #dcfce7;
}

.status.concluído {
  color: #1d4ed8;
  background: #dbeafe;
}

.status.arquivado {
  color: #475569;
  background: #e2e8f0;
}

.project-footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 12px;
  margin-top: 22px;
  padding-top: 14px;
  border-top: 1px solid #e2e8f0;
  color: #64748b;
  font-size: 12px;
}

.empty-state {
  padding: 30px;
  text-align: center;
  color: #64748b;
  background: white;
  border-radius: 10px;
}

@media (max-width: 600px) {
  .page-header,
  .list-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .page-header h1 {
    font-size: 27px;
  }

  .search-input {
    max-width: none;
  }
}
</style>
