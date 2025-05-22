import type { Agent } from '@/types/agent';
import AgentMetrics from './AgentMetrics';

interface AgentCardProps {
  agent: Agent;
  className?: string;
  onSelect?: (agent: Agent) => void;
}

export default function AgentCard({ agent, className = '', onSelect }: AgentCardProps) {
  const { id, name, description, status, lastActive } = agent;
  
  const getStatusColor = () => {
    switch (status?.toLowerCase()) {
      case 'online':
        return 'bg-green-100 text-green-800';
      case 'offline':
        return 'bg-gray-100 text-gray-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  return (
    <div 
      className={`cursor-pointer bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow duration-200 ${className}`}
      onClick={() => onSelect?.(agent)}
    >
      <div className="p-4">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{name}</h3>
            <p className="text-sm text-gray-500">{id}</p>
          </div>
          <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${getStatusColor()}`}>
            {status || 'Unknown'}
          </span>
        </div>
        
        {description && (
          <p className="mt-2 text-sm text-gray-600 line-clamp-2">
            {description}
          </p>
        )}
        
        <div className="mt-4">
          <AgentMetrics agent={agent} />
        </div>
        
        {lastActive && (
          <div className="mt-3 text-xs text-gray-500">
            Last active: {new Date(lastActive).toLocaleString()}
          </div>
        )}
      </div>
    </div>
  );
}
