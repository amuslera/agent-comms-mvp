import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface PlanSubmissionResponse {
  plan_id: string;
  status: string;
  message?: string;
}

export const submitPlan = async (planContent: string): Promise<PlanSubmissionResponse> => {
  try {
    // Try to parse as JSON first
    let parsedContent;
    try {
      parsedContent = JSON.parse(planContent);
    } catch (e) {
      // If not valid JSON, try to parse as YAML
      try {
        const { default: yaml } = await import('yaml');
        parsedContent = yaml.parse(planContent);
      } catch (yamlError) {
        throw new Error('Content is neither valid JSON nor YAML');
      }
    }

    const response = await axios.post(`${API_BASE_URL}/plans/`, {
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
