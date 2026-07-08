import { apiClient } from './client'

export interface Overview {
  host_count: number
  metric_count: number
  point_count: number
}

export async function fetchOverview(): Promise<Overview> {
  const response = await apiClient.get<Overview>('/metrics/overview')
  return response.data
}
