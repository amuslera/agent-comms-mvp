import { useCallback, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Position,
  useNodesState,
  useEdgesState,
  Panel,
  useReactFlow,
  type Node,
  type Edge,
} from 'reactflow';
import TaskNode from './TaskNode';
import type { TaskExecution, TaskNodeData } from '@/types/execution';
import { statusColors } from '@/types/execution';
import { cn } from '@/lib/utils';
import { Loader2, RefreshCw } from 'lucide-react';
import { Button } from '../ui/button';

const nodeTypes = {
  task: TaskNode,
};

interface DagViewerProps {
  tasks: TaskExecution[];
  className?: string;
  loading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
}

export function DagViewer({
  tasks,
  className = '',
  loading = false,
  error = null,
  onRefresh,
}: DagViewerProps) {
  // Convert tasks to nodes and edges for the DAG
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (!tasks || tasks.length === 0) {
      return { nodes: [], edges: [] };
    }

    const nodes: Node<TaskNodeData>[] = [];
    const edges: Edge[] = [];

    // Create nodes
    tasks.forEach((task) => {
      nodes.push({
        id: task.task_id,
        type: 'task',
        position: { x: 0, y: 0 }, // Will be positioned by layout
        data: {
          label: task.task_id.split('-').pop() || task.task_id,
          status: task.status,
          agent: task.agent,
          type: task.type,
          score: task.score,
          retryCount: task.retry_count,
          startedAt: task.started_at,
          completedAt: task.completed_at,
          error: task.error,
        },
      });

      // Create edges for dependencies
      if (task.dependencies && task.dependencies.length > 0) {
        task.dependencies.forEach((depId) => {
          edges.push({
            id: `${depId}-${task.task_id}`,
            source: depId,
            target: task.task_id,
            animated: task.status === 'running',
            style: {
              stroke: task.status === 'failed' ? '#ef4444' : '#94a3b8',
            },
          });
        });
      }
    });

    // Simple layout - this could be enhanced with a proper DAG layout algorithm
    const nodeLayers: Record<string, number> = {};

    // Assign layers based on dependencies
    const assignLayer = (taskId: string): number => {
      if (nodeLayers[taskId] !== undefined) {
        return nodeLayers[taskId];
      }

      const task = tasks.find((t) => t.task_id === taskId);
      if (!task || !task.dependencies || task.dependencies.length === 0) {
        nodeLayers[taskId] = 0;
        return 0;
      }

      const maxDepLayer = Math.max(
        ...task.dependencies.map((depId) => assignLayer(depId))
      );
      nodeLayers[taskId] = maxDepLayer + 1;
      return nodeLayers[taskId];
    };

    tasks.forEach((task) => {
      assignLayer(task.task_id);
    });

    // Calculate positions
    nodes.forEach((node) => {
      const layer = nodeLayers[node.id] || 0;
      const yPos = layer * 200; // Vertical spacing between layers
      
      // Count how many nodes are in this layer
      const layerCount = Object.values(nodeLayers).filter((l) => l === layer).length;
      const layerIndex = Object.values(nodeLayers)
        .slice(0, nodes.findIndex((n) => n.id === node.id))
        .filter((l) => l === layer).length;
      
      // Position nodes in the center of the layer
      const xPos = (layerIndex - (layerCount - 1) / 2) * 300; // Horizontal spacing between nodes
      
      node.position = { x: xPos, y: yPos };
      node.targetPosition = Position.Top;
      node.sourcePosition = Position.Bottom;
    });

    return { nodes, edges };
  }, [tasks]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const { fitView } = useReactFlow();

  // Update nodes and edges when tasks change
  useMemo(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
    setTimeout(() => fitView({ padding: 0.2 }), 100);
  }, [initialNodes, initialEdges, setNodes, setEdges, fitView]);

  const handleRefresh = useCallback(() => {
    if (onRefresh) {
      onRefresh();
    }
  }, [onRefresh]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 bg-muted/20 rounded-md">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading DAG...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-destructive/10 text-destructive rounded-md">
        <p className="font-medium">Failed to load DAG</p>
        <p className="text-sm mt-1">{error}</p>
        {onRefresh && (
          <Button
            variant="outline"
            size="sm"
            className="mt-2"
            onClick={handleRefresh}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        )}
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-muted/20 rounded-md text-muted-foreground">
        No tasks available for this plan
      </div>
    );
  }

  return (
    <div className={cn('h-[600px] w-full bg-background rounded-lg border', className)}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        nodesDraggable
        nodesConnectable={false}
        elementsSelectable
        panOnDrag
        zoomOnScroll
        zoomOnPinch
        panOnScroll
      >
        <Background />
        <Controls />
        <MiniMap />
        <Panel position="top-right" className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => fitView({ padding: 0.2 })}
          >
            Fit View
          </Button>
          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={loading}
            >
              <RefreshCw className={cn('mr-2 h-4 w-4', loading ? 'animate-spin' : '')} />
              Refresh
            </Button>
          )}
        </Panel>
        <Panel position="bottom-left" className="flex flex-wrap gap-2 p-2 bg-background/80 rounded">
          {Object.entries(statusColors).map(([status, color]) => (
            <div key={status} className="flex items-center text-xs">
              <div className={cn('w-3 h-3 rounded-full mr-1', color)} />
              <span className="capitalize">{status}</span>
            </div>
          ))}
        </Panel>
      </ReactFlow>
    </div>
  );
}
