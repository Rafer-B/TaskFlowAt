<script setup lang="ts">
type ActionIconName =
  | 'add'
  | 'archive'
  | 'back'
  | 'calendar'
  | 'check'
  | 'close'
  | 'copy'
  | 'delete'
  | 'edit'
  | 'forward'
  | 'refresh'
  | 'save'
  | 'team'
  | 'tasks'
  | 'today'
  | 'undo'
  | 'user'
  | 'view'

defineProps<{
  name: ActionIconName
}>()

const paths: Record<ActionIconName, string> = {
  add: 'M12 5v14M5 12h14',
  archive: 'M4 7h16v13H4zM3 4h18v3H3zM10 11h4',
  back: 'M19 12H5m7 7-7-7 7-7',
  calendar: 'M5 4h14a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zM16 2v4M8 2v4M3 9h18',
  check: 'm5 12 4 4L19 6',
  close: 'M18 6 6 18M6 6l12 12',
  copy: 'M8 8V4h12v12h-4M4 8h12v12H4z',
  delete: 'M4 7h16M10 11v6M14 11v6M6 7l1 14h10l1-14M9 7V4h6v3',
  edit: 'M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4z',
  forward: 'M5 12h14m-7-7 7 7-7 7',
  refresh: 'M20 7v5h-5M4 17v-5h5M5.5 9a7 7 0 0 1 11.7-2L20 12M4 12l2.8 5a7 7 0 0 0 11.7-2',
  save: 'M5 3h12l4 4v14H3V3zM7 3v6h10V3M7 21v-8h10v8',
  team: 'M16 20v-1.5a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4V20M9.5 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM17 11a3 3 0 1 0 0-6M21 20v-1.5a4 4 0 0 0-3-3.87',
  tasks: 'M9 5h10a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2zM10 12l2 2 4-4M4 7h1M4 12h1M4 17h1',
  today: 'M12 3v18M3 12h18',
  undo: 'M9 14 4 9l5-5M4 9h10a6 6 0 0 1 0 12h-2',
  user: 'M20 21a8 8 0 0 0-16 0M12 13a5 5 0 1 0 0-10 5 5 0 0 0 0 10z',
  view: 'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7zM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',
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
    aria-hidden="true"
    focusable="false"
  >
    <path :d="paths[name]" />
  </svg>
</template>

<style scoped>
svg {
  display: inline-block;
  width: 16px;
  height: 16px;
  flex: 0 0 16px;
  vertical-align: middle;
}
</style>
