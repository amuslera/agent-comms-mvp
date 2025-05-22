import React, { useEffect, useState } from 'react';
import axios from 'axios';
import AgentsList from '@/components/agents/AgentsList';
import { Agent } from '@/types/agent';

// Mock data for testing
const MOCK_AGENTS: Agent[] = [
  {
    id: 'agent-001',
    name: 'Research Agent',
    description: 'Handles research tasks and data gathering',
    status: 'online',
    lastActive: new Date(Date.now() - 1000 * 60 * 5).toISOString(), // 5 minutes ago
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
    description: 'Performs data analysis and generates insights',
    status: 'online',
    lastActive: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 minutes ago
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
    lastActive: new Date(Date.now() - 1000 * 60 * 120).toISOString(), // 2 hours ago
    metrics: {
      averageScore: 0.78,
      successRate: 0.65,
      tasksCompleted: 45,
      tasksFailed: 24,
      lastUpdated: new Date().toISOString(),
    },
  },
  {
    id: 'agent-004',
    name: 'Validation Agent',
    description: 'Validates and verifies data quality',
    status: 'offline',
    lastActive: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
    metrics: {
      averageScore: 0.94,
      successRate: 0.98,
      tasksCompleted: 210,
      tasksFailed: 4,
      lastUpdated: new Date().toISOString(),
    },
  },
];

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [useMockData, setUseMockData] = useState(false);

  useEffect(() => {
    const fetchAgents = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // In a real app, you would make an API call here
        // const response = await axios.get('/api/agents');
        // setAgents(response.data);
        
        // For now, use mock data after a short delay to simulate network request
        setTimeout(() => {
          setAgents(MOCK_AGENTS);
          setLoading(false);
        }, 500);
      } catch (err) {
        console.error('Error fetching agents:', err);
        setError('Failed to load agent metrics. Using mock data instead.');
        setUseMockData(true);
        setAgents(MOCK_AGENTS);
        setLoading(false);
      }
    };

    fetchAgents();
  }, []);

  const handleAgentSelect = (agent: Agent) => {
    console.log('Selected agent:', agent);
    // In a real app, you might navigate to a detail page or show a modal
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Agent Dashboard</h1>
        <p className="text-gray-600">Monitor and manage your AI agents</p>
        
        {useMockData && (
          <div className="mt-4 p-3 bg-yellow-50 text-yellow-700 rounded-md text-sm">
            ⚠️ Using mock data. Connect to your backend to see real agent metrics.
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6">
        <AgentsList 
          agents={agents} 
          onAgentSelect={handleAgentSelect}
          loading={loading}
          error={error}
        />
      </div>
    </div>
  );
                      <span>{(agent.success_rate * 100).toFixed(1)}%</span>
                      <div className="w-24 h-2 bg-gray-200 rounded">
                        <div
                          className={`h-2 rounded ${agent.success_rate >= 0.8 ? 'bg-green-400' : agent.success_rate >= 0.5 ? 'bg-yellow-400' : 'bg-red-400'}`}
                          style={{ width: `${Math.round(agent.success_rate * 100)}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-2 text-sm">
                    <div className="flex items-center gap-2">
                      <span>{agent.average_score.toFixed(2)}</span>
                      <div className="w-24 h-2 bg-gray-200 rounded">
                        <div
                          className={`h-2 rounded ${agent.average_score >= 0.8 ? 'bg-green-400' : agent.average_score >= 0.5 ? 'bg-yellow-400' : 'bg-red-400'}`}
                          style={{ width: `${Math.round(agent.average_score * 100)}%` }}
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