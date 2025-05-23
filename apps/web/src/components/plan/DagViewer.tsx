import { useCallback, useEffect, useMemo, useState } from 'react';
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
  BackgroundVariant,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import TaskNode from './TaskNode';
import type { TaskExecution, TaskNodeData } from '@/types/execution';
import { cn } from '@/lib/utils';
import { Loader2, RefreshCw, Maximize2, Minimize2, Plus, Minus } from 'lucide-react';
import { Button } from '../ui/button';
import { useWindowSize } from 'usehooks-ts';

const nodeTypes = { task: TaskNode };

interface DagViewerProps {
  tasks: TaskExecution[];
  className?: string;
  loading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
}

export function DagViewer({
  tasks = [],
  className = '',
  loading = false,
  error = null,
  onRefresh,
}: DagViewerProps) {
  const { width: windowWidth } = useWindowSize();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const { fitView, zoomIn, zoomOut, setCenter } = useReactFlow();

  // Calculate node positions and create edges
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (!tasks?.length) return { nodes: [], edges: [] };

    const nodes: Node<TaskNodeData>[] = [];
    const edges: Edge[] = [];
    const nodeMap = new Map<string, Node<TaskNodeData>>();
    const dependencies = new Map<string, string[]>();
    const dependents = new Map<string, string[]>();
    const nodeDepths = new Map<string, number>();

    // Initialize nodes and dependency tracking
    tasks.forEach((task) => {
      const node: Node<TaskNodeData> = {
        id: task.task_id,
        type: 'task',
        position: { x: 0, y: 0 },
        data: {
          id: task.task_id,
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
      };
      
      nodes.push(node);
      nodeMap.set(task.task_id, node);
      
      // Initialize dependency tracking
      if (task.dependencies?.length) {
        dependencies.set(task.task_id, [...task.dependencies]);
        task.dependencies.forEach((depId) => {
          if (!dependents.has(depId)) dependents.set(depId, []);
          dependents.get(depId)?.push(task.task_id);
        });
      } else {
        dependencies.set(task.task_id, []);
      }
      
      if (!dependents.has(task.task_id)) {
        dependents.set(task.task_id, []);
      }
    });

    // Calculate node depths using BFS
    const queue: string[] = [];
    const inDegree = new Map<string, number>();
    
    // Initialize in-degree and find root nodes
    nodes.forEach((node) => {
      const deps = dependencies.get(node.id) || [];
      inDegree.set(node.id, deps.length);
      if (deps.length === 0) {
        queue.push(node.id);
        nodeDepths.set(node.id, 0);
      }
    });
    
    // Process nodes in topological order
    let currentIndex = 0;
    while (currentIndex < queue.length) {
      const nodeId = queue[currentIndex++];
      const currentDepth = nodeDepths.get(nodeId) || 0;
      
      dependents.get(nodeId)?.forEach((dependentId) => {
        const remainingDeps = (inDegree.get(dependentId) || 1) - 1;
        inDegree.set(dependentId, remainingDeps);
        nodeDepths.set(dependentId, Math.max(nodeDepths.get(dependentId) || 0, currentDepth + 1));
        if (remainingDeps === 0) queue.push(dependentId);
      });
    }
    
    // Calculate positions
    const HORIZONTAL_SPACING = 280;
    const VERTICAL_SPACING = 220;
    
    // Position nodes
    nodes.forEach((node) => {
      const depth = nodeDepths.get(node.id) || 0;
      const layerNodes = nodes.filter(n => (nodeDepths.get(n.id) || 0) === depth);
      const index = layerNodes.findIndex(n => n.id === node.id);
      const layerNodeCount = layerNodes.length;
      
      node.position = {
        x: (index - (layerNodeCount - 1) / 2) * HORIZONTAL_SPACING,
        y: depth * VERTICAL_SPACING
      };
      node.targetPosition = Position.Top;
      node.sourcePosition = Position.Bottom;
    });
    
    // Create edges
    tasks.forEach((task) => {
      task.dependencies?.forEach((depId, idx) => {
        if (nodeMap.has(depId) && nodeMap.has(task.task_id)) {
          const edgeColor = task.status === 'failed' ? '#ef4444' : 
                         task.status === 'completed' ? '#10b981' : 
                         task.status === 'running' ? '#3b82f6' : '#94a3b8';
          
          edges.push({
            id: `${depId}-${task.task_id}-${idx}`,
            source: depId,
            target: task.task_id,
            animated: task.status === 'running',
            type: 'smoothstep',
            style: { stroke: edgeColor, strokeWidth: 1.5 },
            markerEnd: { type: MarkerType.ArrowClosed, color: edgeColor },
          });
        }
      });
    });

    return { nodes, edges };
  }, [tasks]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes and edges when tasks change
  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
    const timer = setTimeout(() => fitView({ padding: 0.2, duration: 200 }), 100);
    return () => clearTimeout(timer);
  }, [initialNodes, initialEdges, setNodes, setEdges, fitView]);

  // Handle window resize
  useEffect(() => {
    const timer = setTimeout(() => fitView({ padding: 0.2, duration: 200 }), 100);
    return () => clearTimeout(timer);
  }, [windowWidth, fitView]);

  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(!isFullscreen);
    setTimeout(() => fitView({ padding: 0.2, duration: 200 }), 100);
  }, [isFullscreen, fitView]);

  const handleRefresh = useCallback(() => {
    onRefresh?.();
  }, [onRefresh]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 bg-muted/20 rounded-md">
        <div className="flex flex-col items-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mb-2" />
          <span className="text-muted-foreground">Loading DAG...</span>
        </div>
      </div>
    );
  }


  if (error) {
    return (
      <div className="p-4 bg-destructive/10 text-destructive rounded-md">
        <p className="font-medium">Failed to load DAG</p>
        <p className="text-sm mt-1">{error}</p>
        {onRefresh && (
          <div className="mt-3">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              className="flex items-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Retry
            </Button>
          </div>
        )}
      </div>
    );
  }

  if (!tasks.length) {
    return (
      <div className="flex flex-col items-center justify-center h-64 bg-muted/20 rounded-md text-muted-foreground p-4 text-center">
        <p className="mb-2">No tasks available for this plan</p>
        {onRefresh && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className={cn(
      'w-full bg-background rounded-lg border relative',
      isFullscreen ? 'fixed inset-0 z-50' : 'h-[600px]',
      className
    )}>
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
        minZoom={0.2}
        maxZoom={2}
        defaultEdgeOptions={{
          type: 'smoothstep',
          animated: false,
          style: { stroke: '#94a3b8', strokeWidth: 1.5 },
          markerEnd: { type: MarkerType.ArrowClosed, color: '#94a3b8' },
        }}
        proOptions={{ hideAttribution: true }}
      >
        <Background 
          variant={BackgroundVariant.Dots} 
          gap={16} 
          size={1} 
          color="#e2e8f0"
          className="bg-gray-50 dark:bg-gray-900"
        />
        
        {/* Custom controls */}
        <div className="absolute right-4 top-4 flex flex-col gap-2 z-10">
          <div className="bg-white dark:bg-gray-800 rounded-md shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden">
            <button
              onClick={() => zoomIn({ duration: 200 })}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors w-10 h-10 flex items-center justify-center border-b border-gray-200 dark:border-gray-700"
              aria-label="Zoom in"
            >
              <Plus className="h-4 w-4" />
            </button>
            <button
              onClick={() => zoomOut({ duration: 200 })}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors w-10 h-10 flex items-center justify-center border-b border-gray-200 dark:border-gray-700"
              aria-label="Zoom out"
            >
              <Minus className="h-4 w-4" />
            </button>
            <button
              onClick={() => fitView({ padding: 0.2, duration: 200 })}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors w-10 h-10 flex items-center justify-center"
              aria-label="Fit view"
            >
              <Maximize2 className="h-4 w-4" />
            </button>
          </div>
          
          {onRefresh && (
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="bg-white dark:bg-gray-800 p-2 rounded-md shadow-md border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors w-10 h-10 flex items-center justify-center"
              aria-label="Refresh"
            >
              <RefreshCw className={cn('h-4 w-4', loading ? 'animate-spin' : '')} />
            </button>
          )}
          
          <button
            onClick={toggleFullscreen}
            className="bg-white dark:bg-gray-800 p-2 rounded-md shadow-md border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors w-10 h-10 flex items-center justify-center"
            aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          >
            {isFullscreen ? (
              <Minimize2 className="h-4 w-4" />
            ) : (
              <Maximize2 className="h-4 w-4" />
            )}
          </button>
        </div>
        
        <MiniMap 
          nodeColor={(node) => {
            switch (node.data.status) {
              case 'completed': return '#10b981';
              case 'running': return '#3b82f6';
              case 'failed': return '#ef4444';
              case 'pending': return '#f59e0b';
              case 'skipped': return '#9ca3af';
              default: return '#94a3b8';
            }
          }}
          nodeStrokeWidth={3}
          maskColor="rgba(255, 255, 255, 0.5)"
          className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-md border border-gray-200 dark:border-gray-700 shadow-sm"
          style={{
            right: 16,
            bottom: 16,
            width: 180,
            height: 120,
          }}
          zoomable
          pannable
        />
        
        <Panel position="top-left" className="!left-4 !top-4">
          <div className="flex items-center gap-2 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm p-2 rounded-md border border-gray-200 dark:border-gray-700 shadow-sm flex-wrap">
            {[
              { status: 'completed', color: 'bg-green-500', label: 'Completed' },
              { status: 'running', color: 'bg-blue-500', label: 'Running' },
              { status: 'failed', color: 'bg-red-500', label: 'Failed' },
              { status: 'pending', color: 'bg-yellow-500', label: 'Pending' },
              { status: 'skipped', color: 'bg-gray-400', label: 'Skipped' },
            ].map(({ status, color, label }) => (
              <div key={status} className="flex items-center text-xs">
                <div className={`w-3 h-3 rounded-full ${color} mr-1.5`} />
                <span>{label}</span>
              </div>
            ))}
          </div>
        </Panel>
      </ReactFlow>
      
      {isFullscreen && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm px-4 py-2 rounded-full border border-gray-200 dark:border-gray-700 shadow-lg z-10">
          <p className="text-sm font-medium">DAG View - Press ESC or click the button to exit fullscreen</p>
        </div>
      )}
    </div>
  );
}
