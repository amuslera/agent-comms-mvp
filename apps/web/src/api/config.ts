// API configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  AGENTS: '/agents',
  TASKS: '/tasks',
  PLANS: '/plans',
  PLANS_HISTORY: '/plans/history',
  TASKS_RECENT: '/tasks/recent',
  ALERTS: import.meta.env.VITE_ALERT_ENDPOINT || '/alerts',
} as const;

// Type for API endpoints
type ApiEndpoints = typeof API_ENDPOINTS;

// Type for endpoint values
export type ApiEndpoint = ApiEndpoints[keyof ApiEndpoints];
