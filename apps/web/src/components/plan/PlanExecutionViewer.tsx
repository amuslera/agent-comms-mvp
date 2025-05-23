import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Loader2, AlertTriangle, RefreshCw } from 'lucide-react';

export interface TaskExecution {
  task_id: string;
  agent: string;
  type: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'retry';
  score?: number;
  retry_count: number;
  started_at?: string;
  completed_at?: string;
  error?: string;
}

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
    switch (status) {
      case 'completed':
        return <Badge variant="success">Completed</Badge>;
      case 'in_progress':
        return <Badge variant="secondary">In Progress</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      case 'retry':
        return <Badge variant="warning">Retry</Badge>;
      default:
        return <Badge variant="outline">Pending</Badge>;
    }
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
    <Card className={className}>
      <CardHeader>
        <CardTitle>Plan Execution</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-auto max-h-[600px] pr-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Task ID</TableHead>
                <TableHead>Agent</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Score</TableHead>
                <TableHead>Retries</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Completed</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tasks.map((task) => (
                <TableRow key={task.task_id}>
                  <TableCell className="font-medium">{task.task_id}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{task.agent}</Badge>
                  </TableCell>
                  <TableCell className="capitalize">{task.type}</TableCell>
                  <TableCell>{getStatusBadge(task.status)}</TableCell>
                  <TableCell className="text-right">
                    {task.score !== undefined ? `${task.score}%` : 'N/A'}
                  </TableCell>
                  <TableCell>{task.retry_count}</TableCell>
                  <TableCell>{formatDate(task.started_at)}</TableCell>
                  <TableCell>{formatDate(task.completed_at)}</TableCell>
                </TableRow>
              ))}
              {tasks.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                    No tasks found for this plan
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
