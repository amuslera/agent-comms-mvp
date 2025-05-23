import { memo, useMemo } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';
import type { TaskNodeData } from '@/types/execution';
import { cn } from '@/lib/utils';
import { Tooltip } from '@/components/ui/tooltip';
import { 
  AlertCircle, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  HelpCircle, 
  RefreshCw,
  Code2,
  User,
  Timer,
  Calendar
} from 'lucide-react';

// Helper function to get status label
const getStatusLabel = (status: string): string => {
  const statusMap: Record<string, string> = {
    'completed': 'Completed',
    'running': 'Running',
    'pending': 'Pending',
    'failed': 'Failed',
    'skipped': 'Skipped',
    'canceled': 'Canceled'
  };
  return statusMap[status] || status.charAt(0).toUpperCase() + status.slice(1);
};

const TaskNode = ({ data, selected }: NodeProps<TaskNodeData>) => {
  const { 
    label, 
    status, 
    agent, 
    type, 
    score, 
    retryCount,
    startedAt,
    completedAt,
    error,
    id
  } = data;

  // Format date and time for display
  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  // Calculate duration if start time is available
  const getDuration = () => {
    if (!startedAt) return null;
    
    const start = new Date(startedAt);
    const end = completedAt ? new Date(completedAt) : new Date();
    const durationMs = end.getTime() - start.getTime();
    
    // Convert to appropriate units
    if (durationMs < 1000) return { text: '<1s', ms: durationMs };
    if (durationMs < 60000) return { 
      text: `${Math.round(durationMs / 1000)}s`, 
      ms: durationMs 
    };
    
    const minutes = Math.floor(durationMs / 60000);
    const seconds = Math.round((durationMs % 60000) / 1000);
    return { 
      text: `${minutes}m${seconds.toString().padStart(2, '0')}s`,
      ms: durationMs
    };
  };
  
  const duration = getDuration();
  
  // Get status color variants
  const statusColors = useMemo(() => ({
    completed: {
      bg: 'bg-green-50 dark:bg-green-900/20',
      border: 'border-green-200 dark:border-green-800',
      text: 'text-green-700 dark:text-green-300',
      icon: <CheckCircle2 className="h-3.5 w-3.5 text-green-600 dark:text-green-400" />
    },
    running: {
      bg: 'bg-blue-50 dark:bg-blue-900/20',
      border: 'border-blue-200 dark:border-blue-800',
      text: 'text-blue-700 dark:text-blue-300',
      icon: <div className="h-3.5 w-3.5 rounded-full bg-blue-500 dark:bg-blue-400 animate-pulse" />
    },
    pending: {
      bg: 'bg-amber-50 dark:bg-amber-900/20',
      border: 'border-amber-200 dark:border-amber-800',
      text: 'text-amber-700 dark:text-amber-300',
      icon: <Clock className="h-3.5 w-3.5 text-amber-500 dark:text-amber-400" />
    },
    failed: {
      bg: 'bg-red-50 dark:bg-red-900/20',
      border: 'border-red-200 dark:border-red-800',
      text: 'text-red-700 dark:text-red-300',
      icon: <XCircle className="h-3.5 w-3.5 text-red-500 dark:text-red-400" />
    },
    skipped: {
      bg: 'bg-gray-50 dark:bg-gray-800/50',
      border: 'border-gray-200 dark:border-gray-700',
      text: 'text-gray-600 dark:text-gray-400',
      icon: <HelpCircle className="h-3.5 w-3.5 text-gray-400 dark:text-gray-500" />
    }
  }), []);
  
  const currentStatus = statusColors[status as keyof typeof statusColors] || statusColors.pending;

  // Tooltip content for the main node
  const getNodeTooltip = () => (
    <div className="text-sm max-w-xs p-2 space-y-2">
      <div className="font-semibold flex items-center gap-2">
        <Code2 className="h-4 w-4" />
        <span>Task: {label}</span>
      </div>
      
      <div className="grid grid-cols-[auto,1fr] gap-x-3 gap-y-1 text-xs">
        <span className="text-muted-foreground">ID:</span>
        <code className="font-mono text-xs break-all">{id}</code>
        
        <span className="text-muted-foreground">Status:</span>
        <div className="flex items-center gap-1">
          {currentStatus.icon}
          <span>{getStatusLabel(status)}</span>
        </div>
        
        <span className="text-muted-foreground">Agent:</span>
        <div className="flex items-center gap-1">
          <User className="h-3 w-3 opacity-70" />
          <span>{agent || 'N/A'}</span>
        </div>
        
        <span className="text-muted-foreground">Type:</span>
        <span>{type || 'N/A'}</span>
        
        {startedAt && (
          <>
            <span className="text-muted-foreground">Started:</span>
            <div className="flex items-center gap-1">
              <Calendar className="h-3 w-3 opacity-70" />
              <span>{formatDateTime(startedAt)}</span>
            </div>
          </>
        )}
        
        {completedAt && (
          <>
            <span className="text-muted-foreground">Completed:</span>
            <div className="flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3 opacity-70" />
              <span>{formatDateTime(completedAt)}</span>
            </div>
          </>
        )}
        
        {duration && (
          <>
            <span className="text-muted-foreground">Duration:</span>
            <div className="flex items-center gap-1">
              <Timer className="h-3 w-3 opacity-70" />
              <span>{duration.text}</span>
              {status === 'running' && <span className="text-xs text-muted-foreground">(running)</span>}
            </div>
          </>
        )}
        
        {retryCount > 0 && (
          <>
            <span className="text-muted-foreground">Retries:</span>
            <div className="flex items-center gap-1">
              <RefreshCw className="h-3 w-3 opacity-70" />
              <span>{retryCount} {retryCount === 1 ? 'retry' : 'retries'}</span>
            </div>
          </>
        )}
        
        {error && (
          <div className="col-span-2 mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded text-red-700 dark:text-red-300 text-xs">
            <div className="font-medium flex items-center gap-1">
              <AlertCircle className="h-3.5 w-3.5" />
              <span>Error</span>
            </div>
            <div className="mt-1 whitespace-pre-wrap break-words">{error}</div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <Tooltip content={getNodeTooltip()}>
      <div 
        className={cn(
          'p-3 rounded-lg border shadow-sm w-64 transition-all relative group cursor-help',
          currentStatus.bg,
          currentStatus.border,
          'border',
          selected ? 'ring-2 ring-offset-2 ring-blue-500' : 'hover:shadow-md',
          'flex flex-col gap-2',
          'dark:border-opacity-50',
          'transition-all duration-200 ease-in-out',
          'hover:scale-[1.02] hover:z-10',
          'active:scale-100 active:shadow-sm'
        )}
        aria-label={`Task: ${label}. Status: ${getStatusLabel(status)}`}
      >
        {/* Status bar */}
        <div className={cn(
          'absolute top-0 left-0 right-0 h-1.5 rounded-t-lg',
          {
            'bg-green-500': status === 'completed',
            'bg-blue-500': status === 'running',
            'bg-amber-500': status === 'pending',
            'bg-red-500': status === 'failed',
            'bg-gray-400': status === 'skipped',
          }
        )} />
        
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="font-medium text-sm leading-tight line-clamp-2 break-words pr-4">
            {label}
          </div>
          
          <div className={cn(
            'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
            currentStatus.text,
            'bg-white/70 dark:bg-black/30',
            'border',
            currentStatus.border,
            'shadow-xs',
            'whitespace-nowrap',
            'transition-colors duration-200'
          )}>
            {currentStatus.icon}
            <span className="ml-1.5">{getStatusLabel(status)}</span>
          </div>
        </div>

        {/* Metadata */}
        <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-xs -mx-1 px-1 py-1 bg-white/30 dark:bg-black/10 rounded">
          <div className="truncate col-span-2 flex items-center">
            <User className="h-3 w-3 mr-1 opacity-60 flex-shrink-0" />
            <span className="truncate font-medium" title={agent}>
              {agent || 'No agent'}
            </span>
          </div>
          
          <div className="truncate flex items-center">
            <Code2 className="h-3 w-3 mr-1 opacity-60 flex-shrink-0" />
            <span className="truncate" title={type}>
              {type || 'No type'}
            </span>
          </div>
          
          {duration && (
            <div className="truncate flex items-center">
              <Timer className="h-3 w-3 mr-1 opacity-60 flex-shrink-0" />
              <span className="truncate">
                {duration.text}
                {status === 'running' && '...'}
              </span>
            </div>
          )}
          
          {score !== undefined && (
            <div className="col-span-2 mt-1">
              <div className="flex items-center gap-2">
                <div className="w-full bg-gray-200/50 dark:bg-gray-700/50 rounded-full h-1.5 overflow-hidden">
                  <div 
                    className={cn(
                      'h-full rounded-full',
                      score > 80 ? 'bg-green-500' :
                      score > 50 ? 'bg-amber-500' : 'bg-red-500',
                      'transition-all duration-500 ease-out'
                    )}
                    style={{ width: `${score}%` }}
                    aria-label={`Score: ${score}%`}
                  />
                </div>
                <span className="text-xs font-medium whitespace-nowrap">
                  {score}%
                </span>
              </div>
            </div>
          )}
        </div>
        
        {/* Error message */}
        {error && (
          <div className="mt-1 p-1.5 bg-red-50/80 dark:bg-red-900/30 text-red-600 dark:text-red-300 text-xs rounded flex items-start gap-1.5">
            <AlertCircle className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />
            <div className="line-clamp-2 break-words">{error}</div>
          </div>
        )}
        
        {/* Handles */}
        <Handle 
          type="target" 
          position={Position.Top} 
          className="w-2.5 h-2.5 bg-gray-400 dark:bg-gray-500 border-2 border-white dark:border-gray-800 opacity-0 group-hover:opacity-100 transition-opacity"
          style={{ top: -6 }}
          aria-label="Task input connector"
        />
        <Handle 
          type="source" 
          position={Position.Bottom} 
          className="w-2.5 h-2.5 bg-gray-400 dark:bg-gray-500 border-2 border-white dark:border-gray-800 opacity-0 group-hover:opacity-100 transition-opacity"
          style={{ bottom: -6 }}
          aria-label="Task output connector"
        />
      </div>
    </Tooltip>
  );
};

export default memo(TaskNode);
