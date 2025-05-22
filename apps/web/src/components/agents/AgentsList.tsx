import React, { useState, useMemo } from 'react';
import { Agent } from '../../types/agent';
import AgentCard from './AgentCard';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';

interface AgentsListProps {
  agents: Agent[];
  onAgentSelect?: (agent: Agent) => void;
  className?: string;
}

type SortField = 'name' | 'score' | 'tasks' | 'status';
type SortOrder = 'asc' | 'desc';

const AgentsList: React.FC<AgentsListProps> = ({ agents, onAgentSelect, className = '' }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const filteredAndSortedAgents = useMemo(() => {
    // Filter agents based on search term
    const filtered = agents.filter(agent => 
      agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      agent.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      agent.description?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Sort agents
    return [...filtered].sort((a, b) => {
      let comparison = 0;
      
      switch (sortField) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'score':
          comparison = (a.metrics?.averageScore || 0) - (b.metrics?.averageScore || 0);
          break;
        case 'tasks':
          const aTasks = (a.metrics?.tasksCompleted || 0) + (a.metrics?.tasksFailed || 0);
          const bTasks = (b.metrics?.tasksCompleted || 0) + (b.metrics?.tasksFailed || 0);
          comparison = aTasks - bTasks;
          break;
        case 'status':
          comparison = (a.status || '').localeCompare(b.status || '');
          break;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }, [agents, searchTerm, sortField, sortOrder]);

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex-1">
          <Input
            type="text"
            placeholder="Search agents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full"
          />
        </div>
        
        <div className="flex gap-2">
          <Select
            value={sortField}
            onValueChange={(value) => setSortField(value as SortField)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="name">Name</SelectItem>
              <SelectItem value="score">Score</SelectItem>
              <SelectItem value="tasks">Task Count</SelectItem>
              <SelectItem value="status">Status</SelectItem>
            </SelectContent>
          </Select>
          
          <Select
            value={sortOrder}
            onValueChange={(value) => setSortOrder(value as SortOrder)}
          >
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Order" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="asc">Ascending</SelectItem>
              <SelectItem value="desc">Descending</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {filteredAndSortedAgents.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No agents found matching your search.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAndSortedAgents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onSelect={onAgentSelect}
              className="h-full"
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default AgentsList;
