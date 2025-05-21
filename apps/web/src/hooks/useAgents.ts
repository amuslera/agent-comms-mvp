import { useState, useEffect } from 'react';
import { Agent, getAgents } from '../api/agentApi';

interface UseAgentsResult {
  agents: Agent[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Custom hook to fetch and manage agents data
 * @param status Optional status filter
 * @returns Object containing agents, loading state, error, and refresh function
 */
export const useAgents = (status?: string): UseAgentsResult => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAgents(status);
      setAgents(data.agents);
    } catch (err) {
      setError('Failed to fetch agents. Please try again later.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchAgents();
    
    // Set up polling every 10 seconds
    const intervalId = setInterval(fetchAgents, 10000);
    
    // Clean up interval on unmount
    return () => clearInterval(intervalId);
  }, [status]);

  return {
    agents,
    loading,
    error,
    refresh: fetchAgents,
  };
};
