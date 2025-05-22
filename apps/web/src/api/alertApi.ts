import axios from 'axios';
import { API_ENDPOINTS } from './config';

export interface AlertPolicy {
  id: string;
  name: string;
  description?: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  condition: Record<string, unknown>;
  actions: Array<{
    type: 'webhook' | 'email' | 'slack' | 'pagerduty';
    target: string;
    config?: Record<string, unknown>;
  }>;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface AlertPoliciesResponse {
  policies: AlertPolicy[];
  count: number;
}

/**
 * Fetches all alert policies
 */
export const getAlertPolicies = async (): Promise<AlertPoliciesResponse> => {
  try {
    const response = await axios.get<AlertPoliciesResponse>(
      `${API_ENDPOINTS.ALERTS}/policies`
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching alert policies:', error);
    throw error;
  }
};

/**
 * Creates a new alert policy
 */
export const createAlertPolicy = async (
  policy: Omit<AlertPolicy, 'id' | 'created_at' | 'updated_at'>
): Promise<AlertPolicy> => {
  try {
    const response = await axios.post<AlertPolicy>(
      `${API_ENDPOINTS.ALERTS}/policies`,
      policy
    );
    return response.data;
  } catch (error) {
    console.error('Error creating alert policy:', error);
    throw error;
  }
};

/**
 * Updates an existing alert policy
 */
export const updateAlertPolicy = async (
  id: string,
  updates: Partial<Omit<AlertPolicy, 'id' | 'created_at' | 'updated_at'>>
): Promise<AlertPolicy> => {
  try {
    const response = await axios.put<AlertPolicy>(
      `${API_ENDPOINTS.ALERTS}/policies/${id}`,
      updates
    );
    return response.data;
  } catch (error) {
    console.error(`Error updating alert policy ${id}:`, error);
    throw error;
  }
};

/**
 * Deletes an alert policy
 */
export const deleteAlertPolicy = async (id: string): Promise<void> => {
  try {
    await axios.delete(`${API_ENDPOINTS.ALERTS}/policies/${id}`);
  } catch (error) {
    console.error(`Error deleting alert policy ${id}:`, error);
    throw error;
  }
};
