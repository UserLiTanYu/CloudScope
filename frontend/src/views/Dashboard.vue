<script setup lang="ts">
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
  type GridComponentOption,
  type LegendComponentOption,
  type TooltipComponentOption,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { BarSeriesOption, LineSeriesOption, PieSeriesOption } from 'echarts/charts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

import { fetchDashboard, type DashboardData, type HostHealthRow } from '../api/metrics'

type ChartOption = echarts.ComposeOption<
  | BarSeriesOption
  | GridComponentOption
  | LegendComponentOption
  | LineSeriesOption
  | PieSeriesOption
  | TooltipComponentOption
>

echarts.use([
  BarChart,
  CanvasRenderer,
  GridComponent,
  LegendComponent,
  LineChart,
  PieChart,
  TooltipComponent,
])

defineOptions({ name: 'CloudScopeDashboard' })

const dashboard = ref<DashboardData | null>(null)
const loading = ref(true)
const error = ref('')
const trendChartRef = ref<HTMLDivElement | null>(null)
const diskChartRef = ref<HTMLDivElement | null>(null)
const locationChartRef = ref<HTMLDivElement | null>(null)

let trendChart: echarts.ECharts | null = null
let diskChart: echarts.ECharts | null = null
let locationChart: echarts.ECharts | null = null

const summary = computed(() => dashboard.value?.summary ?? [])
const hostRows = computed(() => dashboard.value?.host_health.slice(0, 10) ?? [])
const businessTopLists = computed(() => [
  { title: 'CPU TOP 主机', unit: '%', rows: dashboard.value?.cpu_top ?? [] },
  { title: '内存 TOP 主机', unit: 'MB', rows: dashboard.value?.memory_top ?? [] },
  { title: '网络流量 TOP 主机', unit: 'MB/s', rows: dashboard.value?.network_top ?? [] },
])
const updatedAt = computed(() => new Date().toLocaleString('zh-CN', { hour12: false }))

function formatNumber(value: number | string, digits = 2): string {
  const numberValue = Number(value)
  if (!Number.isFinite(numberValue)) {
    return String(value)
  }
  return numberValue.toLocaleString('zh-CN', {
    maximumFractionDigits: digits,
    minimumFractionDigits: numberValue % 1 === 0 ? 0 : digits,
  })
}

function metricValue(row: HostHealthRow, key: 'cpu_usage' | 'disk_util' | 'mem_used'): string {
  const value = row[key]
  if (value === null) {
    return '-'
  }
  const suffix = key === 'mem_used' ? ' MB' : '%'
  return `${formatNumber(value)}${suffix}`
}

function renderCharts(): void {
  if (!dashboard.value || !trendChartRef.value || !diskChartRef.value || !locationChartRef.value) {
    return
  }

  trendChart ??= echarts.init(trendChartRef.value)
  diskChart ??= echarts.init(diskChartRef.value)
  locationChart ??= echarts.init(locationChartRef.value)

  const trendLabels = dashboard.value.trends[0]?.points.map((point) =>
    point.collect_time.slice(5, 16).replace('T', ' '),
  )

  const trendOption: ChartOption = {
    color: ['#74d4b3', '#8db7ff', '#f0b35a'],
    tooltip: { trigger: 'axis' },
    legend: {
      top: 0,
      textStyle: { color: '#b8c7d9' },
    },
    grid: { left: 44, right: 18, top: 44, bottom: 34 },
    xAxis: {
      type: 'category',
      data: trendLabels,
      axisLine: { lineStyle: { color: '#344252' } },
      axisLabel: { color: '#94a3b8' },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.14)' } },
      axisLabel: { color: '#94a3b8' },
    },
    series: dashboard.value.trends.map((series) => ({
      name: series.name,
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: series.points.map((point) => Number(point.value)),
    })),
  }

  const diskItems = dashboard.value.disk_top
  const diskOption: ChartOption = {
    color: ['#74d4b3'],
    tooltip: { trigger: 'axis' },
    grid: { left: 92, right: 24, top: 12, bottom: 20 },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.14)' } },
    },
    yAxis: {
      type: 'category',
      data: diskItems.map((item) => `${item.hostid} ${item.mod}`),
      inverse: true,
      axisLabel: { color: '#c7d2e1', width: 84, overflow: 'truncate' },
      axisLine: { lineStyle: { color: '#344252' } },
    },
    series: [
      {
        name: '磁盘利用率',
        type: 'bar',
        data: diskItems.map((item) => Number(item.value)),
        barWidth: 12,
        itemStyle: { borderRadius: [0, 4, 4, 0] },
      },
    ],
  }

  trendChart.setOption(trendOption)
  diskChart.setOption(diskOption)

  const locationOption: ChartOption = {
    color: ['#74d4b3', '#8db7ff', '#f0b35a', '#d98282', '#a78bfa'],
    tooltip: { trigger: 'item' },
    legend: {
      bottom: 0,
      textStyle: { color: '#b8c7d9' },
    },
    series: [
      {
        name: '机房分布',
        type: 'pie',
        radius: ['44%', '68%'],
        center: ['50%', '44%'],
        avoidLabelOverlap: true,
        label: { color: '#dbe6f3' },
        data: dashboard.value.location_distribution,
      },
    ],
  }

  locationChart.setOption(locationOption)
}

function resizeCharts(): void {
  trendChart?.resize()
  diskChart?.resize()
  locationChart?.resize()
}

onMounted(async () => {
  try {
    dashboard.value = await fetchDashboard()
    await nextTick()
    renderCharts()
    window.addEventListener('resize', resizeCharts)
  } catch {
    error.value = '数据加载失败，请确认后端 API 与 MySQL 已启动'
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  trendChart?.dispose()
  diskChart?.dispose()
  locationChart?.dispose()
})
</script>

<template>
  <main class="dashboard">
    <header class="topbar">
      <div>
        <p class="eyebrow">
          CloudScope
        </p>
        <h1>云监控可视化大屏</h1>
      </div>
      <div class="runtime">
        <span :class="['status-dot', { loading }]" />
        <span>{{ loading ? '加载中' : '实时数据已连接' }}</span>
        <strong>{{ updatedAt }}</strong>
      </div>
    </header>

    <section
      v-if="error"
      class="empty-state"
    >
      {{ error }}
    </section>

    <template v-else>
      <section class="summary-grid">
        <article
          v-for="item in summary"
          :key="item.key"
          class="summary-tile"
        >
          <span>{{ item.label }}</span>
          <strong>{{ formatNumber(item.value) }}</strong>
          <em v-if="item.unit">{{ item.unit }}</em>
        </article>
      </section>

      <section class="screen-grid">
        <article class="panel trend-panel">
          <div class="panel-heading">
            <h2>核心指标趋势</h2>
            <span>近 24 小时平均值</span>
          </div>
          <div
            ref="trendChartRef"
            class="chart"
          />
        </article>

        <article class="panel">
          <div class="panel-heading">
            <h2>磁盘利用率 TOP</h2>
            <span>最新采集批次</span>
          </div>
          <div
            ref="diskChartRef"
            class="chart"
          />
        </article>

        <article class="panel business-panel">
          <div class="panel-heading">
            <h2>业务指标排行</h2>
            <span>近 24 小时聚合</span>
          </div>
          <div class="business-grid">
            <section
              v-for="group in businessTopLists"
              :key="group.title"
              class="rank-block"
            >
              <h3>{{ group.title }}</h3>
              <div class="rank-list">
                <div
                  v-for="(item, index) in group.rows.slice(0, 5)"
                  :key="`${group.title}-${item.hostid}`"
                  class="rank-row"
                >
                  <span class="rank-index">{{ index + 1 }}</span>
                  <span class="rank-host">
                    <strong>{{ item.hostid }}</strong>
                    <small>{{ item.hostname }}</small>
                  </span>
                  <span class="rank-value">{{ formatNumber(item.value) }} {{ group.unit }}</span>
                </div>
              </div>
            </section>
          </div>
        </article>

        <article class="panel location-panel">
          <div class="panel-heading">
            <h2>主机机房分布</h2>
            <span>按 location1 统计</span>
          </div>
          <div
            ref="locationChartRef"
            class="chart"
          />
        </article>

        <article class="panel host-panel">
          <div class="panel-heading">
            <h2>主机健康明细</h2>
            <span>近 24 小时聚合</span>
          </div>
          <div class="host-table">
            <div class="host-table-head">
              <span>主机</span>
              <span>位置</span>
              <span>CPU</span>
              <span>内存</span>
              <span>磁盘</span>
            </div>
            <div
              v-for="row in hostRows"
              :key="row.hostid"
              class="host-row"
            >
              <span>
                <strong>{{ row.hostid }}</strong>
                <small>{{ row.hostname }}</small>
              </span>
              <span>{{ row.location }}</span>
              <span>{{ metricValue(row, 'cpu_usage') }}</span>
              <span>{{ metricValue(row, 'mem_used') }}</span>
              <span>{{ metricValue(row, 'disk_util') }}</span>
            </div>
          </div>
        </article>
      </section>
    </template>
  </main>
</template>
