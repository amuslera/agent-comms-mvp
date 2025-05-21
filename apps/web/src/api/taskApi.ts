import axios from 'axios';
import { API_BASE_URL, API_ENDPOINTS } from './config';

export interface Task {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  agent_id?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
  metadata?: Record<string, unknown>;
}

export interface TaskListResponse {
  tasks: Task[];
  count: number;
}

interface GetTasksParams {
  status?: string;
  agent_id?: string;
  limit?: number;
  offset?: number;
}

/**
 * Fetches a list of tasks from the API
 * @param params Query parameters for filtering and pagination
 * @returns Promise with the list of tasks and count
 */
export const getTasks = async (params?: GetTasksParams): Promise<TaskListResponse> => {
  try {
    const response = await axios.get<TaskListResponse>(
      `${API_BASE_URL}${API_ENDPOINTS.TASKS}`,
      { params }
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching tasks:', error);
    throw error;
  }
};

/**
 * Fetches a single task by ID
 * @param taskId The ID of the task to fetch
 * @returns Promise with the task details
 */
export const getTaskById = async (taskId: string): Promise<Task> => {
  try {
    const response = await axios.get<Task>(
      `${API_BASE_URL}${API_ENDPOINTS.TASKS}/${taskId}`
    );
    return response.data;
  } catch (error) {
    console.error(`Error fetching task ${taskId}:`, error);
    throw error;
  }
};
