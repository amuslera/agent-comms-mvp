import type { Node, Edge } from 'reactflow';

export type TaskStatus = 
  | 'waiting' 
  | 'ready' 
  | 'running' 
  | 'completed' 
  | 'failed' 
  | 'skipped'
  | 'pending' 
  | 'in_progress' 
  | 'retry';

export interface TaskExecution {
  task_id: string;
  agent: string;
  type: string;
  status: TaskStatus;
  score?: number;
  retry_count: number;
  started_at?: string;
  completed_at?: string;
  error?: string;
  dependencies?: string[];
  layer?: number;
}

export interface PlanExecution {
  plan_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  tasks: TaskExecution[];
}

export interface TaskNodeData {
  id?: string;
  label: string;
  status: TaskStatus;
  agent: string;
  type: string;
  score?: number;
  retryCount: number;
  startedAt?: string;
  completedAt?: string;
  error?: string;
}

export type TaskNode = Node<TaskNodeData>;
export type TaskEdge = Edge;

export interface DagData {
  nodes: TaskNode[];
  edges: TaskEdge[];
}

export const statusColors: Record<TaskStatus, string> = {
  waiting: 'bg-gray-200 text-gray-800',
  ready: 'bg-blue-100 text-blue-800',
  running: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  skipped: 'bg-gray-100 text-gray-500',
  pending: 'bg-gray-200 text-gray-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  retry: 'bg-orange-100 text-orange-800',
};

export const statusIcons: Record<TaskStatus, string> = {
  waiting: '⏳',
  ready: '🔵',
  running: '🔄',
  completed: '✅',
  failed: '❌',
  skipped: '⏭️',
  pending: '⏳',
  in_progress: '🔄',
  retry: '🔄',
};
