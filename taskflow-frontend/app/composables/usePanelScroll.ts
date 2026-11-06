import type { Ref } from 'vue'
import { nextTick } from 'vue'

export async function scrollToPanel(panel: Ref<HTMLElement | null>): Promise<void> {
  await nextTick()
  panel.value?.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  })
}
