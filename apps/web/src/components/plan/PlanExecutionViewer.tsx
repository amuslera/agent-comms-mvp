import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Loader2, AlertTriangle, RefreshCw } from 'lucide-react';
import type { TaskExecution } from '@/types/execution';
import { statusColors } from '@/types/execution';
import { cn } from '@/lib/utils';

interface PlanExecutionViewerProps {
  tasks: TaskExecution[];
  className?: string;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export function PlanExecutionViewer({ 
  tasks, 
  className = '',
  loading = false,
  error = null,
  onRetry
}: PlanExecutionViewerProps) {
  const getStatusBadge = (status: string) => {
    const statusText = status
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
      
    const colorClass = statusColors[status as keyof typeof statusColors] || 'bg-gray-100 text-gray-800';
      
    return (
      <Badge className={cn('whitespace-nowrap', colorClass)}>
        {statusText}
      </Badge>
    );
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Loading tasks...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="py-8 text-center">
          <AlertTriangle className="h-8 w-8 mx-auto text-destructive mb-2" />
          <p className="text-destructive font-medium">Failed to load tasks</p>
          <p className="text-sm text-muted-foreground mt-1">{error}</p>
          {onRetry && (
            <Button 
              variant="outline" 
              className="mt-4"
              onClick={onRetry}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry
            </Button>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={className}>
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Task Details</h3>
        {tasks.map((task) => (
          <div key={task.task_id} className="border rounded-lg p-4 space-y-2">
            <div className="flex justify-between items-start">
              <h4 className="font-medium">{task.task_id}</h4>
              <span className={cn('px-2 py-1 rounded text-xs', statusColors[task.status] || 'bg-gray-100 text-gray-800')}>
                {task.status.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
              <div>
                <span className="text-muted-foreground">Agent:</span> {task.agent}
              </div>
              <div>
                <span className="text-muted-foreground">Type:</span> {task.type}
              </div>
              <div>
                <span className="text-muted-foreground">Score:</span> {task.score ? `${(task.score * 100).toFixed(1)}%` : 'N/A'}
              </div>
              <div>
                <span className="text-muted-foreground">Retries:</span> {task.retry_count}
              </div>
            </div>
            {task.dependencies && task.dependencies.length > 0 && (
              <div className="text-sm">
                <span className="text-muted-foreground">Dependencies:</span> {task.dependencies.join(', ')}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
