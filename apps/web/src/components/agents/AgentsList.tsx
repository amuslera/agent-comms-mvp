import type { Agent } from '@/types/agent';
import AgentCard from './AgentCard';

interface AgentsListProps {
  agents: Agent[];
  onAgentSelect: (agent: Agent) => void;
  loading?: boolean;
  error?: string | null;
}

export default function AgentsList({ agents, onAgentSelect, loading = false, error = null }: AgentsListProps) {
  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center p-8 text-red-500">
        <p>{error}</p>
      </div>
    );
  }

  if (!agents || agents.length === 0) {
    return (
      <div className="text-center p-8 text-gray-500">
        <p>No agents found</p>
      </div>
    );
  }


  return (
    <div className="space-y-4">
      {agents.map((agent) => (
        <AgentCard
          key={agent.id}
          agent={agent}
          onSelect={() => onAgentSelect(agent)}
          className="cursor-pointer hover:bg-gray-50 transition-colors"
        />
      ))}
    </div>
  );
}
