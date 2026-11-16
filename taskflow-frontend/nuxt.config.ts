// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: false },
  hooks: {
    'pages:extend'(pages) {
      const routesByPage: Record<string, string[]> = {
        'tasks.vue': [
          '/tasks/create',
          '/tasks/:taskId',
          '/tasks/:taskId/edit',
        ],
        'my-work.vue': ['/my-work/tasks/:taskId/update'],
        'projects.vue': [
          '/projects/create',
          '/projects/:projectId',
          '/projects/:projectId/edit',
          '/projects/:projectId/members',
        ],
        'teams.vue': [
          '/teams/create',
          '/teams/:teamId',
          '/teams/:teamId/edit',
        ],
        'users/index.vue': ['/users/create'],
        'users/[id].vue': ['/users/:id/edit'],
        'settings.vue': [
          '/settings/profile/edit',
          '/settings/password/edit',
        ],
        'calendar.vue': [
          '/calendar/events/new',
          '/calendar/events/:eventId',
          '/calendar/events/:eventId/edit',
        ],
      }

      for (const page of pages) {
        const pageFile = page.file?.replace(/\\/g, '/')
        const matchingRoutes = Object.entries(routesByPage).find(([file]) =>
          pageFile?.endsWith(file),
        )
        if (matchingRoutes) {
          const aliases = matchingRoutes[1]
          page.alias = [...(page.alias ?? []), ...aliases]
        }
      }
    },
  },

  css: ['~/assets/css/main.css'],

  app: {
    head: {
      htmlAttrs: { lang: 'pt-PT' },
      title: 'TaskFlow',
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap',
        },
      ],
    }
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000'
    }
  }
})