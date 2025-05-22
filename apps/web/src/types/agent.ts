export interface AgentMetrics {
  averageScore: number;
  successRate: number;
  tasksCompleted: number;
  tasksFailed: number;
  lastUpdated: string;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  status: 'online' | 'offline' | 'error' | 'idle';
  lastActive: string;
  metrics: AgentMetrics;
}
