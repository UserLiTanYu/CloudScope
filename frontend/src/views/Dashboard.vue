<script setup lang="ts">
import * as echarts from 'echarts/core'
import { BarChart, GaugeChart, LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
  type GridComponentOption,
  type LegendComponentOption,
  type TooltipComponentOption,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type {
  BarSeriesOption,
  GaugeSeriesOption,
  LineSeriesOption,
  PieSeriesOption,
} from 'echarts/charts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

import { fetchDashboard, type DashboardData, type HostHealthRow } from '../api/metrics'

type ChartOption = echarts.ComposeOption<
  | BarSeriesOption
  | GaugeSeriesOption
  | GridComponentOption
  | LegendComponentOption
  | LineSeriesOption
  | PieSeriesOption
  | TooltipComponentOption
>

echarts.use([
  BarChart,
  CanvasRenderer,
  GaugeChart,
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
const currentTime = ref(new Date().toLocaleString('zh-CN', { hour12: false }))

const idcDistChartRef = ref<HTMLDivElement | null>(null)
const hwModelChartRef = ref<HTMLDivElement | null>(null)
const riskRankChartRef = ref<HTMLDivElement | null>(null)
const trendChartRef = ref<HTMLDivElement | null>(null)
const healthGaugeRef = ref<HTMLDivElement | null>(null)
const networkChartRef = ref<HTMLDivElement | null>(null)
const diskTopChartRef = ref<HTMLDivElement | null>(null)

let idcDistChart: echarts.ECharts | null = null
let hwModelChart: echarts.ECharts | null = null
let riskRankChart: echarts.ECharts | null = null
let trendChart: echarts.ECharts | null = null
let healthGauge: echarts.ECharts | null = null
let networkChart: echarts.ECharts | null = null
let diskTopChart: echarts.ECharts | null = null
let clockInterval: ReturnType<typeof setInterval> | null = null
const resizeObservers: ResizeObserver[] = []

const summary = computed(() => dashboard.value?.summary ?? [])
const hostHealthAll = computed(() => dashboard.value?.host_health ?? [])

const healthScore = computed(() => {
  const rows = dashboard.value?.host_health ?? []
  if (rows.length === 0) return 0
  const healthy = rows.filter((r) => {
    const cpuOk = r.cpu_usage === null || Number(r.cpu_usage) <= 80
    const diskOk = r.disk_util === null || Number(r.disk_util) <= 85
    const memOk = r.mem_used === null || Number(r.mem_used) <= 90000
    return cpuOk && diskOk && memOk
  }).length
  return Math.round((healthy / rows.length) * 100)
})

const modelDistribution = computed(() => {
  const rows = dashboard.value?.host_health ?? []
  const map = new Map<string, number>()
  for (const row of rows) {
    const key = row.model || 'Unknown'
    map.set(key, (map.get(key) ?? 0) + 1)
  }
  return Array.from(map.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
})

const riskRankData = computed(() => {
  const d = dashboard.value
  if (!d) return []
  const scores = new Map<
    string,
    { hostid: string; hostname: string; cpu: number; mem: number; net: number }
  >()
  for (const item of d.cpu_top) {
    scores.set(item.hostid, {
      hostid: item.hostid,
      hostname: item.hostname,
      cpu: Number(item.value),
      mem: 0,
      net: 0,
    })
  }
  for (const item of d.memory_top) {
    const entry = scores.get(item.hostid) ?? {
      hostid: item.hostid,
      hostname: item.hostname,
      cpu: 0,
      mem: 0,
      net: 0,
    }
    entry.mem = Number(item.value)
    scores.set(item.hostid, entry)
  }
  for (const item of d.network_top) {
    const entry = scores.get(item.hostid) ?? {
      hostid: item.hostid,
      hostname: item.hostname,
      cpu: 0,
      mem: 0,
      net: 0,
    }
    entry.net = Number(item.value)
    scores.set(item.hostid, entry)
  }
  return Array.from(scores.values())
    .map((s) => ({
      hostid: s.hostid,
      hostname: s.hostname,
      riskScore: s.cpu + s.mem / 1280 + s.net * 2,
    }))
    .sort((a, b) => b.riskScore - a.riskScore)
    .slice(0, 10)
})

const alarmStream = computed(() => {
  const rows = dashboard.value?.host_health ?? []
  const alarms: Array<{
    hostid: string
    hostname: string
    type: string
    value: string
    severity: 'critical' | 'warning'
  }> = []
  for (const row of rows) {
    if (row.cpu_usage !== null && Number(row.cpu_usage) > 80) {
      alarms.push({
        hostid: row.hostid,
        hostname: row.hostname,
        type: 'CPU',
        value: `${formatNumber(row.cpu_usage)}%`,
        severity: Number(row.cpu_usage) > 95 ? 'critical' : 'warning',
      })
    }
    if (row.disk_util !== null && Number(row.disk_util) > 85) {
      alarms.push({
        hostid: row.hostid,
        hostname: row.hostname,
        type: 'Disk',
        value: `${formatNumber(row.disk_util)}%`,
        severity: Number(row.disk_util) > 95 ? 'critical' : 'warning',
      })
    }
    if (row.mem_used !== null && Number(row.mem_used) > 90000) {
      alarms.push({
        hostid: row.hostid,
        hostname: row.hostname,
        type: 'Memory',
        value: `${formatNumber(row.mem_used)} MB`,
        severity: Number(row.mem_used) > 110000 ? 'critical' : 'warning',
      })
    }
  }
  return alarms.sort((a) => (a.severity === 'critical' ? -1 : 1))
})

const networkTrafficData = computed(() => {
  const d = dashboard.value
  if (!d) return { labels: [], values: [] }
  const netSeries = d.trends.find((t) => t.name === '入站带宽')
  if (!netSeries) return { labels: [], values: [] }
  return {
    labels: netSeries.points.map((p) => p.collect_time.slice(11, 16)),
    values: netSeries.points.map((p) => Number(p.value)),
  }
})

function formatNumber(value: number | string, digits = 2): string {
  const numberValue = Number(value)
  if (!Number.isFinite(numberValue)) return String(value)
  return numberValue.toLocaleString('zh-CN', {
    maximumFractionDigits: digits,
    minimumFractionDigits: numberValue % 1 === 0 ? 0 : digits,
  })
}

function metricValue(row: HostHealthRow, key: 'cpu_usage' | 'disk_util' | 'mem_used'): string {
  const value = row[key]
  if (value === null) return '-'
  const suffix = key === 'mem_used' ? ' MB' : '%'
  return `${formatNumber(value)}${suffix}`
}

function healthClass(row: HostHealthRow): string {
  const cpu = row.cpu_usage !== null ? Number(row.cpu_usage) : 0
  const disk = row.disk_util !== null ? Number(row.disk_util) : 0
  const mem = row.mem_used !== null ? Number(row.mem_used) : 0
  if (cpu > 95 || disk > 95 || mem > 110000) return 'critical'
  if (cpu > 80 || disk > 85 || mem > 90000) return 'warning'
  return 'healthy'
}

function observeResize(el: HTMLDivElement, getChart: () => echarts.ECharts | null): void {
  const observer = new ResizeObserver(() => {
    const chart = getChart()
    if (chart && !chart.isDisposed()) {
      chart.resize()
    }
  })
  observer.observe(el)
  resizeObservers.push(observer)
}

function renderCharts(): void {
  if (!dashboard.value) return

  const neonColors = ['#00f0ff', '#74d4b3', '#f0b35a', '#a78bfa', '#ff6b9d', '#d98282']
  const axisLineColor = '#344252'
  const gridLineColor = 'rgba(148, 163, 184, 0.12)'
  const labelColor = '#94a3b8'

  // IDC Distribution Donut
  if (idcDistChartRef.value) {
    idcDistChart ??= echarts.init(idcDistChartRef.value)
    idcDistChart.setOption({
      color: neonColors,
      tooltip: { trigger: 'item' },
      legend: {
        orient: 'vertical',
        right: 8,
        top: 'center',
        itemGap: 12,
        textStyle: { color: '#b8c7d9', fontSize: 12 },
      },
      series: [
        {
          name: 'IDC Distribution',
          type: 'pie',
          radius: ['44%', '68%'],
          center: ['34%', '52%'],
          avoidLabelOverlap: true,
          label: { show: false },
          emphasis: {
            itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0, 240, 255, 0.5)' },
          },
          data: dashboard.value.location_distribution,
        },
      ],
    } as ChartOption)
  }

  // Hardware Models Donut
  if (hwModelChartRef.value) {
    hwModelChart ??= echarts.init(hwModelChartRef.value)
    hwModelChart.setOption({
      color: neonColors,
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: {
        orient: 'vertical',
        right: 8,
        top: 'center',
        itemGap: 10,
        textStyle: { color: '#b8c7d9', fontSize: 12 },
      },
      series: [
        {
          name: 'Hardware Models',
          type: 'pie',
          radius: ['42%', '66%'],
          center: ['34%', '52%'],
          avoidLabelOverlap: true,
          label: { show: false },
          emphasis: {
            itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0, 240, 255, 0.5)' },
          },
          data: modelDistribution.value,
        },
      ],
    } as ChartOption)
  }

  // Risk Ranking TOP10
  if (riskRankChartRef.value) {
    riskRankChart ??= echarts.init(riskRankChartRef.value)
    riskRankChart.setOption({
      color: ['#ff6b9d'],
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 92, right: 28, top: 18, bottom: 32 },
      xAxis: {
        type: 'value',
        axisLabel: { color: labelColor },
        splitLine: { lineStyle: { color: gridLineColor } },
      },
      yAxis: {
        type: 'category',
        data: riskRankData.value.map((r) => r.hostid),
        inverse: true,
        axisLabel: { color: '#c7d2e1', fontSize: 12 },
        axisLine: { lineStyle: { color: axisLineColor } },
      },
      series: [
        {
          name: 'Risk Score',
          type: 'bar',
          data: riskRankData.value.map((r) => Number(r.riskScore.toFixed(1))),
          barWidth: 14,
          itemStyle: {
            borderRadius: [0, 4, 4, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: '#ff6b9d' },
              { offset: 1, color: '#d98282' },
            ]),
          },
        },
      ],
    } as ChartOption)
  }

  // Core Metrics Trend
  if (trendChartRef.value) {
    trendChart ??= echarts.init(trendChartRef.value)
    const trendLabels = dashboard.value.trends[0]?.points.map((point) =>
      point.collect_time.slice(5, 16).replace('T', ' '),
    )
    trendChart.setOption({
      color: ['#00f0ff', '#74d4b3', '#f0b35a'],
      tooltip: { trigger: 'axis' },
      legend: {
        top: 0,
        itemGap: 18,
        textStyle: { color: '#b8c7d9', fontSize: 12 },
      },
      grid: { left: 64, right: 26, top: 58, bottom: 44 },
      xAxis: {
        type: 'category',
        data: trendLabels,
        axisLine: { lineStyle: { color: axisLineColor } },
        axisLabel: { color: labelColor, fontSize: 11 },
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: gridLineColor } },
        axisLabel: { color: labelColor },
      },
      series: dashboard.value.trends.map((series) => ({
        name: series.name,
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 240, 255, 0.25)' },
            { offset: 1, color: 'rgba(0, 240, 255, 0.02)' },
          ]),
        },
        data: series.points.map((point) => Number(point.value)),
      })),
    } as ChartOption)
  }

  // Health Gauge
  if (healthGaugeRef.value) {
    healthGauge ??= echarts.init(healthGaugeRef.value)
    healthGauge.setOption({
      series: [
        {
          type: 'gauge',
          startAngle: 220,
          endAngle: -40,
          min: 0,
          max: 100,
          splitNumber: 10,
          radius: '82%',
          axisLine: {
            lineStyle: {
              width: 12,
              color: [
                [0.3, '#d98282'],
                [0.7, '#f0b35a'],
                [1, '#74d4b3'],
              ],
            },
          },
          pointer: {
            itemStyle: { color: '#e8eef8' },
            length: '60%',
            width: 6,
          },
          axisTick: { distance: -12, length: 6, lineStyle: { color: '#fff', width: 1 } },
          splitLine: { distance: -14, length: 14, lineStyle: { color: '#fff', width: 2 } },
          axisLabel: { color: labelColor, distance: 18, fontSize: 10 },
          detail: {
            valueAnimation: true,
            formatter: '{value}%',
            color: '#e8eef8',
            fontSize: 30,
            fontWeight: 700,
            offsetCenter: [0, '58%'],
          },
          title: {
            offsetCenter: [0, '78%'],
            color: '#94a3b8',
            fontSize: 12,
          },
          data: [{ value: healthScore.value, name: 'Healthy Hosts' }],
        },
      ],
    })
  }

  // Network Traffic 24H
  if (networkChartRef.value) {
    networkChart ??= echarts.init(networkChartRef.value)
    networkChart.setOption({
      color: ['#00f0ff'],
      tooltip: { trigger: 'axis' },
      grid: { left: 54, right: 22, top: 28, bottom: 38 },
      xAxis: {
        type: 'category',
        data: networkTrafficData.value.labels,
        axisLine: { lineStyle: { color: axisLineColor } },
        axisLabel: { color: labelColor, fontSize: 11 },
        boundaryGap: false,
      },
      yAxis: {
        type: 'value',
        name: 'MB/s',
        nameTextStyle: { color: labelColor },
        splitLine: { lineStyle: { color: gridLineColor } },
        axisLabel: { color: labelColor },
      },
      series: [
        {
          name: 'Inbound',
          type: 'line',
          smooth: true,
          showSymbol: false,
          data: networkTrafficData.value.values,
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(0, 240, 255, 0.35)' },
              { offset: 1, color: 'rgba(0, 240, 255, 0.02)' },
            ]),
          },
          lineStyle: { width: 2 },
        },
      ],
    } as ChartOption)
  }

  // Disk TOP10
  if (diskTopChartRef.value) {
    diskTopChart ??= echarts.init(diskTopChartRef.value)
    const diskItems = dashboard.value.disk_top
    diskTopChart.setOption({
      color: ['#00f0ff'],
      tooltip: { trigger: 'axis' },
      grid: { left: 104, right: 28, top: 18, bottom: 36 },
      xAxis: {
        type: 'value',
        axisLabel: { color: labelColor },
        splitLine: { lineStyle: { color: gridLineColor } },
      },
      yAxis: {
        type: 'category',
        data: diskItems.map((item) => `${item.hostid} ${item.mod}`),
        inverse: true,
        axisLabel: { color: '#c7d2e1', width: 84, overflow: 'truncate' },
        axisLine: { lineStyle: { color: axisLineColor } },
      },
      series: [
        {
          name: 'Disk Usage',
          type: 'bar',
          data: diskItems.map((item) => Number(item.value)),
          barWidth: 12,
          itemStyle: {
            borderRadius: [0, 4, 4, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: '#00f0ff' },
              { offset: 1, color: '#74d4b3' },
            ]),
          },
        },
      ],
    } as ChartOption)
  }
}

onMounted(async () => {
  try {
    dashboard.value = await fetchDashboard()
    await nextTick()
    renderCharts()

    // Set up ResizeObservers for each chart container
    if (idcDistChartRef.value) observeResize(idcDistChartRef.value, () => idcDistChart)
    if (hwModelChartRef.value) observeResize(hwModelChartRef.value, () => hwModelChart)
    if (riskRankChartRef.value) observeResize(riskRankChartRef.value, () => riskRankChart)
    if (trendChartRef.value) observeResize(trendChartRef.value, () => trendChart)
    if (healthGaugeRef.value) observeResize(healthGaugeRef.value, () => healthGauge)
    if (networkChartRef.value) observeResize(networkChartRef.value, () => networkChart)
    if (diskTopChartRef.value) observeResize(diskTopChartRef.value, () => diskTopChart)

    clockInterval = setInterval(() => {
      currentTime.value = new Date().toLocaleString('zh-CN', { hour12: false })
    }, 1000)
  } catch {
    error.value = '数据加载失败，请确认后端 API 与 MySQL 已启动'
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  if (clockInterval) clearInterval(clockInterval)

  // Clean up ResizeObservers
  for (const observer of resizeObservers) {
    observer.disconnect()
  }
  resizeObservers.length = 0

  // Dispose ECharts instances
  idcDistChart?.dispose()
  hwModelChart?.dispose()
  riskRankChart?.dispose()
  trendChart?.dispose()
  healthGauge?.dispose()
  networkChart?.dispose()
  diskTopChart?.dispose()
})
</script>

<template>
  <main class="dashboard">
    <header class="noc-topbar">
      <div class="noc-title">
        <p class="eyebrow">
          CLOUDSCOPE
        </p>
        <h1>云监控 NOC 大屏</h1>
      </div>
      <div class="noc-clock">
        {{ currentTime }}
      </div>
      <div class="noc-badges">
        <div
          v-for="item in summary.slice(0, 5)"
          :key="item.key"
          class="noc-badge"
        >
          <strong>{{ formatNumber(item.value) }}</strong>
          <span>{{ item.label }}</span>
        </div>
      </div>
    </header>

    <section
      v-if="error"
      class="empty-state"
    >
      {{ error }}
    </section>

    <template v-else>
      <section class="noc-grid">
        <!-- Row 1, Col 1: IDC Distribution -->
        <article class="panel" style="grid-area: idcDistribution">
          <div class="panel-heading">
            <h2>机房分布</h2>
            <span>IDC Distribution</span>
          </div>
          <div
            ref="idcDistChartRef"
            class="chart-area"
          />
        </article>

        <!-- Row 1, Col 2: Core Metrics 7-Day Trend -->
        <article class="panel" style="grid-area: coreTrend">
          <div class="panel-heading">
            <h2>核心指标 7 日走势</h2>
            <span>7 Days x 24 Hours Trend</span>
          </div>
          <div
            ref="trendChartRef"
            class="chart-area"
          />
        </article>

        <!-- Row 1, Col 3: Network Traffic 24H -->
        <article class="panel" style="grid-area: networkTraffic">
          <div class="panel-heading">
            <h2>网络流量 24H</h2>
            <span>Network Traffic 24H</span>
          </div>
          <div
            ref="networkChartRef"
            class="chart-area"
          />
        </article>

        <!-- Row 2, Col 1: Server Models -->
        <article class="panel" style="grid-area: serverModels">
          <div class="panel-heading">
            <h2>硬件型号分布</h2>
            <span>Server Models</span>
          </div>
          <div
            ref="hwModelChartRef"
            class="chart-area"
          />
        </article>

        <!-- Row 2, Col 2: Health Gauge -->
        <article class="panel" style="grid-area: healthGauge">
          <div class="panel-heading">
            <h2>今日健康仪表盘</h2>
            <span>Health Gauge</span>
          </div>
          <div
            ref="healthGaugeRef"
            class="chart-area"
          />
        </article>

        <!-- Row 2, Col 3: Disk TOP10 -->
        <article class="panel" style="grid-area: diskTop10">
          <div class="panel-heading">
            <h2>磁盘读写 TOP10</h2>
            <span>Disk Read/Write TOP10</span>
          </div>
          <div
            ref="diskTopChartRef"
            class="chart-area"
          />
        </article>

        <!-- Row 3, Col 1: Risk Ranking TOP10 -->
        <article class="panel" style="grid-area: riskRanking">
          <div class="panel-heading">
            <h2>风险排行 TOP10</h2>
            <span>Risk Ranking</span>
          </div>
          <div
            ref="riskRankChartRef"
            class="chart-area"
          />
        </article>

        <!-- Row 3, Col 2: Host Health Matrix -->
        <article class="panel panel-matrix" style="grid-area: hostHealthMatrix">
          <div class="panel-heading">
            <h2>主机健康矩阵</h2>
            <span>Host Health Matrix</span>
          </div>
          <div class="matrix-scroll">
            <div class="host-matrix-grid">
              <div
                v-for="row in hostHealthAll"
                :key="row.hostid"
                :class="['matrix-cell', healthClass(row)]"
                :title="`${row.hostname}: CPU ${metricValue(row, 'cpu_usage')}, Disk ${metricValue(row, 'disk_util')}`"
              >
                <span class="matrix-label">{{ row.hostid }}</span>
              </div>
            </div>
          </div>
        </article>

        <!-- Row 3, Col 3: Alarm Stream -->
        <article class="panel panel-alarm" style="grid-area: alarmStream">
          <div class="panel-heading">
            <h2>实时告警流</h2>
            <span>Live Alarm Stream</span>
          </div>
          <div class="alarm-scroll">
            <div
              v-for="(alarm, i) in alarmStream"
              :key="i"
              :class="['alarm-item', `alarm-${alarm.severity}`]"
            >
              <span class="alarm-severity">{{ alarm.severity === 'critical' ? '!!' : '!' }}</span>
              <span class="alarm-host">{{ alarm.hostid }}</span>
              <span class="alarm-type">{{ alarm.type }}</span>
              <span class="alarm-value">{{ alarm.value }}</span>
            </div>
            <div
              v-if="alarmStream.length === 0"
              class="alarm-empty"
            >
              暂无活跃告警
            </div>
          </div>
        </article>
      </section>
    </template>
  </main>
</template>
