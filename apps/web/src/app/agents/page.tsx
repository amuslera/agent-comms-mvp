'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'react-hot-toast';
import AgentsList from '@/components/agents/AgentsList';
import { Agent } from '@/types/agent';

// API endpoint
const API_URL = '/api/metrics/agents';

// Mock data for development
const MOCK_AGENTS: Agent[] = [
  {
    id: 'agent-001',
    name: 'Research Agent',
    description: 'Handles research tasks and data gathering',
    status: 'online',
    lastActive: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    metrics: {
      averageScore: 0.92,
      successRate: 0.95,
      tasksCompleted: 124,
      tasksFailed: 6,
      lastUpdated: new Date().toISOString(),
    },
  },
  {
    id: 'agent-002',
    name: 'Analysis Agent',
    description: 'Performs data analysis and insights generation',
    status: 'online',
    lastActive: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    metrics: {
      averageScore: 0.87,
      successRate: 0.82,
      tasksCompleted: 89,
      tasksFailed: 19,
      lastUpdated: new Date().toISOString(),
    },
  },
  {
    id: 'agent-003',
    name: 'Reporting Agent',
    description: 'Generates reports and summaries',
    status: 'error',
    lastActive: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
    metrics: {
      averageScore: 0.78,
      successRate: 0.65,
      tasksCompleted: 45,
      tasksFailed: 24,
      lastUpdated: new Date().toISOString(),
    },
  },
];

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const isDev = process.env.NODE_ENV === 'development';
  const [useMockData, setUseMockData] = useState(isDev);

  const fetchAgentMetrics = async () => {
    try {
      setLoading(true);

      if (useMockData) {
        // Use mock data in development
        await new Promise(resolve => setTimeout(resolve, 500)); // Simulate network delay
        setAgents(MOCK_AGENTS);
        setLastUpdated(new Date().toLocaleTimeString());
        setError(null);
      } else {
        // Fetch from API in production
        const response = await axios.get(API_URL);
        if (response.data && Array.isArray(response.data)) {
          setAgents(response.data);
          setLastUpdated(new Date().toLocaleTimeString());
          setError(null);
        } else {
          throw new Error('Invalid response format');
        }
      }
    } catch (err) {
      console.error('Failed to fetch agent metrics:', err);
      const errorMessage = 'Failed to load agent metrics. Using mock data instead.';
      setError(errorMessage);
      toast.error(errorMessage);

      // Fallback to mock data on error in development
      if (isDev) {
        setUseMockData(true);
        setAgents(MOCK_AGENTS);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgentMetrics();

    // Refresh data every 30 seconds
    const intervalId = setInterval(fetchAgentMetrics, 30000);

    return () => clearInterval(intervalId);
  }, [useMockData, isDev]);

  // Handle manual refresh
  const handleRefresh = () => {
    fetchAgentMetrics();
    toast.success('Refreshing agent metrics...');
  };

  const handleAgentSelect = (agent: Agent) => {
    console.log('Selected agent:', agent);
    // In a real app, you might navigate to a detail page or show a modal
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Agent Metrics</h1>
          <p className="text-sm text-gray-500 mt-1">
            {lastUpdated && `Last updated: ${lastUpdated}`}
            {useMockData && ' (Using mock data)'}
          </p>
        </div>
        <div className="flex gap-2">
          {isDev && (
            <button
              onClick={() => setUseMockData(!useMockData)}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {useMockData ? 'Use Real Data' : 'Use Mock Data'}
            </button>
          )}
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Refreshing...' : 'Refresh Data'}
          </button>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <AgentsList
          agents={agents}
          onAgentSelect={handleAgentSelect}
          loading={loading}
          error={error}
        />
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border-l-4 border-red-400">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-2 text-sm">{agent.retry_count != null ? agent.retry_count : 'N/A'}</td>
                </tr>
              ))}
              {agents.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-gray-400">No agent metrics found.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
} 