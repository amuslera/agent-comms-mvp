import axios from 'axios';
import { API_BASE_URL, API_ENDPOINTS } from './config';

export interface Agent {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'inactive' | 'error';
  description: string;
  role: string;
  capabilities: string[];
  last_active?: string;
  tasks_completed: number;
  tasks_failed: number;
  tasks_in_progress: number;
}

export interface AgentListResponse {
  agents: Agent[];
  count: number;
}
/**
 * Fetches a list of all agents from the API
 * @param status Optional status filter
 * @returns Promise with the list of agents and count
 */
export const getAgents = async (status?: string): Promise<AgentListResponse> => {
  try {
    const response = await axios.get<AgentListResponse>(
      `${API_BASE_URL}${API_ENDPOINTS.AGENTS}`,
      { params: status ? { status } : {} }
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching agents:', error);
    throw error;
  }
};

/**
 * Fetches a single agent by ID
 * @param agentId The ID of the agent to fetch
 * @returns Promise with the agent details
 */
export const getAgentById = async (agentId: string): Promise<Agent> => {
  try {
    const response = await axios.get<Agent>(
      `${API_BASE_URL}${API_ENDPOINTS.AGENTS}/${agentId}`
    );
    return response.data;
  } catch (error) {
    console.error(`Error fetching agent ${agentId}:`, error);
    throw error;
  }
};
