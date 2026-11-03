<script setup lang="ts">
export type SidebarIconName =
  | 'dashboard'
  | 'my-work'
  | 'projects'
  | 'tasks'
  | 'users'
  | 'calendar'
  | 'teams'
  | 'reports'
  | 'settings'
  | 'logout'
  | 'help'
  | 'search'
  | 'notifications'

defineProps<{
  name: SidebarIconName
}>()

const iconPaths: Record<SidebarIconName, string> = {
  dashboard: 'M3.5 3.5h7v7h-7zM13.5 3.5h7v4h-7zM13.5 9.5h7v11h-7zM3.5 12.5h7v8h-7z',
  'my-work': 'M12 3.5l2.55 5.17 5.7.83-4.12 4.02.97 5.68L12 16.52l-5.1 2.68.97-5.68-4.12-4.02 5.7-.83z',
  projects: 'M3.5 7.5h7l2 2h8v9a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2zM3.5 7.5v-2a2 2 0 0 1 2-2h4l2 2h5',
  tasks: 'M9 5.5h10a1.5 1.5 0 0 1 1.5 1.5v11a1.5 1.5 0 0 1-1.5 1.5H9a1.5 1.5 0 0 1-1.5-1.5v-11A1.5 1.5 0 0 1 9 5.5zM10.5 12l2 2 4-4M4 7h1M4 12h1M4 17h1',
  users: 'M16 20v-1.5a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4V20M9.5 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM17 4.3a3.5 3.5 0 0 1 0 6.7M21 20v-1.5a4 4 0 0 0-3-3.87',
  calendar: 'M5 4.5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-12a2 2 0 0 1 2-2zM16 2.5v4M8 2.5v4M3 9.5h18M7 13h.01M12 13h.01M17 13h.01M7 17h.01M12 17h.01',
  teams: 'M16 20v-1.5a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4V20M9.5 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM17 11a3 3 0 1 0 0-6M21 20v-1.5a4 4 0 0 0-3-3.87',
  reports: 'M4 20.5h16M6.5 17V11M12 17V5M17.5 17v-8',
  settings: 'M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7zM19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-1.8 3.12-.08-.03a1.7 1.7 0 0 0-1.82.3l-.07.06h-3.6l-.02-.08a1.7 1.7 0 0 0-1.24-1.28l-.09-.02-1.8-3.12.06-.06a1.7 1.7 0 0 0 .34-1.88l-.03-.08v-3.6l.08-.02a1.7 1.7 0 0 0 1.28-1.24l.02-.09 3.12-1.8.06.06a1.7 1.7 0 0 0 1.88.34l.08-.03h3.6l.02.08a1.7 1.7 0 0 0 1.24 1.28l.09.02 1.8 3.12-.06.06A1.7 1.7 0 0 0 19.4 15z',
  logout: 'M10 4H5.5A1.5 1.5 0 0 0 4 5.5v13A1.5 1.5 0 0 0 5.5 20H10M14 8l4 4-4 4M8 12h10',
  help: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM9.7 9a2.4 2.4 0 1 1 4.08 1.7c-.98.97-1.78 1.22-1.78 2.8M12 17h.01',
  search: 'M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM16 16l4.5 4.5',
  notifications: 'M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4',
}
</script>

<template>
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    focusable="false"
    aria-hidden="true"
  >
    <path :d="iconPaths[name]" />
  </svg>
</template>

<style scoped>
svg {
  display: block;
  width: 19px;
  height: 19px;
}
</style>
