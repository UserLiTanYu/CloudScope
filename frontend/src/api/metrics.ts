import { apiClient } from './client'

export interface Overview {
  host_count: number
  metric_count: number
  point_count: number
}

export interface SummaryMetric {
  key: string
  label: string
  value: number | string
  unit: string
}

export interface MetricPoint {
  collect_time: string
  value: string
}

export interface TrendSeries {
  name: string
  unit: string
  points: MetricPoint[]
}

export interface TopMetricItem {
  hostid: string
  hostname: string
  mod: string
  value: string
  unit: string
}

export interface HostHealthRow {
  hostid: string
  hostname: string
  owner: string
  model: string
  location: string
  cpu_usage: string | null
  mem_used: string | null
  disk_util: string | null
}

export interface DistributionItem {
  name: string
  value: number
}

export interface DashboardData {
  summary: SummaryMetric[]
  trends: TrendSeries[]
  disk_top: TopMetricItem[]
  cpu_top: TopMetricItem[]
  memory_top: TopMetricItem[]
  network_top: TopMetricItem[]
  location_distribution: DistributionItem[]
  host_health: HostHealthRow[]
}

export async function fetchOverview(): Promise<Overview> {
  const response = await apiClient.get<Overview>('/metrics/overview')
  return response.data
}

export async function fetchDashboard(): Promise<DashboardData> {
  const response = await apiClient.get<DashboardData>('/metrics/dashboard')
  return response.data
}
