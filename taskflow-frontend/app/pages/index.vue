<script setup lang="ts">
// Dados temporários para desenhar o dashboard.
// Posteriormente, serão carregados a partir do FastAPI.

const stats = [
    {label: 'Projetos ativos', value: 4, icon:'📁'},
    {label: 'Tarefas em curso', value: 12, icon:'⚡'},
    {label: 'Tarefas concluídas', value: 8, icon:'✓'},
    {label: 'Tarefas bloqueadas', value: 2, icon:'!'}
]

//Exemplos de tarefas para visualizar o design.
const tasks = [
    {
        title: 'Definir os requisitos do TaskFlow',
        project: 'Projeto TaskFlow',
        priority: 'Alta',
        status: 'Em curso'
    },

    {
        title: 'Criar o modelo de dados',
        project: 'Projeto TaskFlow',
        priority: 'Média',
        status: 'Concluída'
    },

    {
        title: 'Preparar a documentação',
        project: 'Projeto académico',
        priority: 'Baixa',
        status: 'Por iniciar'
    }
]

</script>

<template>
    <main class="dashboard">
        <!-- Cabeçalho da página. -->
         <header class="page-header">
            <div>
                <p class="eyebrow">ESPAÇO DE TRABALHO</p>
                <h1>Dashboard</h1>
                <p class="subtitle">
                    Organiza os teus projetos e acompanha o teu progresso.
                </p>
            </div>

            <NuxtLink to="/projects" class="primary-button">
                + Ver Projetos
            </NuxtLink>
         </header>

         <!-- Indicadores Principais -->
          <section class="stats-grid" aria-label="Resumo dos projetos">
            <article v-for="stat in stats" :key="stat.label" class="stat-card">
                <div class="stat-top">
                    <span>{{ stat.label }}</span>
                    <span aria-hidden="true">{{ stat.icon }}</span>
                </div>

                <strong class="stat-value">{{ stat.value }}</strong>
            
            </article>
          </section>

          <!-- Lista de tarefas -->
           <section class="content-card">
                <div class="section-header">
                    <div>
                        <h2>tarefas recentes</h2>
                        <p>Um resumo das atividades da equipa.</p>
                    </div>
                    <NuxtLink to="/tasks" class="text-Link">
                        Ver todas
                    </NuxtLink>
                </div>

                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Tarefa</th>
                                <th>Projeto</th>
                                <th>Prioridade</th>
                                <th>Estado</th>
                            </tr>
                        </thead>

                        <tbody>
                            <tr v-for="task in tasks" :key="task.title">
                                <td class="task-title">{{ task.title }}</td>
                                <td>{{ task.project }}</td>
                                <td>{{ task.priority }}</td>
                                <td>
                                    <span class="status-label">
                                        {{ task.status }}
                                    
                                    </span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
           </section>
    </main>
</template>