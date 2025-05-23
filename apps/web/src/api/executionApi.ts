import axios from 'axios';
import { API_BASE_URL, API_ENDPOINTS } from './config';

export interface TaskExecution {
  task_id: string;
  agent: string;
  type: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'retry';
  score?: number;
  retry_count: number;
  started_at?: string;
  completed_at?: string;
  error?: string;
}

export interface PlanExecution {
  plan_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  tasks: TaskExecution[];
}

export const getPlanExecution = async (planId: string): Promise<PlanExecution> => {
  try {
    const response = await axios.get<PlanExecution>(
      `${API_BASE_URL}${API_ENDPOINTS.PLANS}/${planId}/execution`
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching plan execution:', error);
    throw error;
  }
};

export const getRecentPlanExecutions = async (limit = 5): Promise<PlanExecution[]> => {
  try {
    const response = await axios.get<PlanExecution[]>(
      `${API_BASE_URL}${API_ENDPOINTS.PLANS}/recent`,
      { params: { limit } }
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching recent plan executions:', error);
    return [];
  }
};
