<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchOverview, type Overview } from '../api/metrics'

const overview = ref<Overview | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    overview.value = await fetchOverview()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <main class="dashboard">
    <section class="hero">
      <div>
        <p class="eyebrow">CloudScope</p>
        <h1>云监控可视化大屏</h1>
      </div>
      <div class="status">{{ loading ? '加载中' : '已连接' }}</div>
    </section>

    <section class="metrics">
      <article>
        <span>主机数量</span>
        <strong>{{ overview?.host_count ?? '-' }}</strong>
      </article>
      <article>
        <span>指标数量</span>
        <strong>{{ overview?.metric_count ?? '-' }}</strong>
      </article>
      <article>
        <span>采集点数</span>
        <strong>{{ overview?.point_count ?? '-' }}</strong>
      </article>
    </section>
  </main>
</template>
