import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';
import { statusColors, statusIcons } from '@/types/execution';
import type { TaskNodeData } from '@/types/execution';
import { cn } from '@/lib/utils';

const TaskNode = ({ data, selected }: NodeProps<TaskNodeData>) => {
  const { 
    label, 
    status, 
    agent, 
    type, 
    score, 
    retryCount,
    startedAt,
    error 
  } = data;

  return (
    <div 
      className={cn(
        'p-3 rounded-lg border shadow-sm w-64 transition-all',
        statusColors[status as keyof typeof statusColors],
        selected ? 'ring-2 ring-offset-2 ring-blue-500' : ''
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-medium truncate">{label}</h3>
        <span className="text-sm opacity-75">{statusIcons[status]}</span>
      </div>
      
      <div className="text-xs space-y-1">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Agent:</span>
          <span className="font-medium">{agent}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Type:</span>
          <span className="font-medium capitalize">{type}</span>
        </div>
        {score !== undefined && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Score:</span>
            <span className="font-medium">{score}%</span>
          </div>
        )}
        {retryCount > 0 && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Retries:</span>
            <span className="font-medium">{retryCount}</span>
          </div>
        )}
        {startedAt && (
          <div className="text-xs text-muted-foreground truncate">
            Started: {new Date(startedAt).toLocaleString()}
          </div>
        )}
        {error && (
          <div className="mt-1 p-1 bg-red-50 text-red-600 text-xs rounded">
            {error}
          </div>
        )}
      </div>

      <Handle 
        type="target" 
        position={Position.Top} 
        className="w-2 h-2 bg-gray-400"
      />
      <Handle 
        type="source" 
        position={Position.Bottom} 
        className="w-2 h-2 bg-gray-400"
      />
    </div>
  );
};

export default memo(TaskNode);
