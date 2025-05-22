import axios from 'axios';
import { API_BASE_URL, API_ENDPOINTS } from './config';

export interface PlanSubmissionResponse {
  plan_id: string;
  status: string;
  message?: string;
}

export interface PlanHistoryItem {
  plan_id: string;
  submitted_at: string;
  status: string;
  agent_count: number;
}

export interface PlanHistoryResponse {
  plans: PlanHistoryItem[];
  count: number;
}

export const submitPlan = async (planContent: string): Promise<PlanSubmissionResponse> => {
  try {
    // Try to parse as JSON first
    try {
      JSON.parse(planContent);
    } catch (e) {
      // If not valid JSON, try to parse as YAML
      try {
        const { default: yaml } = await import('yaml');
        yaml.parse(planContent);
      } catch (yamlError) {
        throw new Error('Content is neither valid JSON nor YAML');
      }
    }

    const response = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.PLANS}/`, {
      plan: planContent,
      execute: false
    }, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      throw new Error(`Failed to submit plan: ${message}`);
    }
    throw error;
  }
};

export const getPlanHistory = async (params?: { limit?: number; offset?: number }): Promise<PlanHistoryResponse> => {
  try {
    const response = await axios.get<PlanHistoryResponse>(
      `${API_BASE_URL}${API_ENDPOINTS.PLANS_HISTORY}`,
      { params }
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching plan history:', error);
    throw error;
  }
};
