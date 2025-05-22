import React, { useCallback, useMemo, useEffect, useState } from 'react';
import ReactFlow, {
  type Node,
  type Edge,
  type NodeTypes as ReactFlowNodeTypes,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  Panel,
} from 'reactflow';
// @ts-ignore - We'll create this utility
import { getLayoutedElements } from '../utils/layout';
import 'reactflow/dist/style.css';
import styled from '@emotion/styled';

// Custom node types
import { TaskNode } from './nodes/TaskNode';

// Define the plan task type based on the API model
interface PlanTask {
  task_id: string;
  agent: string;
  type: string;
  description: string;
  priority: string;
  status?: 'pending' | 'running' | 'success' | 'failed' | 'retry';
  deadline?: string;
  content: Record<string, any>;
  dependencies: string[];
  max_retries?: number;
  fallback_agent?: string;
  timeout?: string;
  duration_sec?: number;
  score?: number;
  notes?: string;
  notifications?: Record<string, string[]>;
}

interface PlanMetadata {
  plan_id: string;
  version: string;
  created?: string;
  description: string;
  priority: string;
  timeout?: string;
}

export interface Plan {
  metadata: PlanMetadata;
  tasks: PlanTask[];
}

// Styled components
const FlowContainer = styled.div`
  width: 100%;
  height: 100%;
  min-height: 600px;
  background: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e9ecef;
`;

const Tooltip = styled.div`
  position: absolute;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  border-radius: 4px;
  font-size: 12px;
  pointer-events: none;
  z-index: 100;
  max-width: 300px;
  white-space: pre-wrap;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
`;

const StatusBadge = styled.span<{ status?: string }>`
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.7em;
  font-weight: 600;
  text-transform: capitalize;
  margin-left: 8px;
  background-color: ${({ status }) => {
    switch (status) {
      case 'success':
        return '#198754';
      case 'running':
        return '#0d6efd';
      case 'failed':
        return '#dc3545';
      case 'retry':
        return '#fd7e14';
      case 'pending':
      default:
        return '#6c757d';
    }
  }};
  color: white;
`;

const nodeTypes: ReactFlowNodeTypes = {
  task: TaskNode,
};

interface PlanDAGViewerProps {
  plan: Plan;
  onNodeClick?: (taskId: string) => void;
  className?: string;
}

const PlanDAGViewerComponent: React.FC<PlanDAGViewerProps> = ({
  plan,
  onNodeClick,
  className,
}) => {
  const { fitView } = useReactFlow();
  const [tooltip, setTooltip] = useState<{
    content: string;
    x: number;
    y: number;
    visible: boolean;
  }>({ content: '', x: 0, y: 0, visible: false });

  // Convert plan tasks to nodes and edges with layout
  const { initialNodes, initialEdges } = useMemo(() => {
    const nodes: Node[] = plan.tasks.map((task) => ({
      id: task.task_id,
      type: 'task',
      position: { x: 0, y: 0 }, // Will be calculated by layout
      data: {
        ...task,
        label: task.task_id,
        onClick: () => onNodeClick?.(task.task_id),
        onMouseEnter: (e: React.MouseEvent, node: Node) => {
          const rect = (e.target as HTMLElement).getBoundingClientRect();
          setTooltip({
            content: `Agent: ${task.agent}\n` +
                    `Status: ${task.status || 'pending'}\n` +
                    (task.duration_sec ? `Duration: ${task.duration_sec.toFixed(2)}s\n` : '') +
                    (task.score ? `Score: ${(task.score * 100).toFixed(1)}%\n` : '') +
                    (task.notes ? `Notes: ${task.notes}` : ''),
            x: rect.left + window.scrollX,
            y: rect.top + window.scrollY - 10,
            visible: true,
          });
        },
        onMouseLeave: () => {
          setTooltip(prev => ({ ...prev, visible: false }));
        },
      },
    }));

    const edges: Edge[] = plan.tasks.flatMap((task) =>
      task.dependencies.map((depId) => ({
        id: `${depId}-${task.task_id}`,
        source: depId,
        target: task.task_id,
        type: 'smoothstep',
        animated: task.status === 'running',
        style: {
          stroke: '#adb5bd',
          strokeWidth: 2,
        },
      }))
    );

    // Apply layout to nodes
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      nodes,
      edges,
      'TB' // Top to bottom layout
    );

    return { initialNodes: layoutedNodes, initialEdges: layoutedEdges };
  }, [plan, onNodeClick]);

  // State for nodes and edges
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes and edges when initial data changes
  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
    
    // Fit view after a small delay to allow DOM updates
    const timer = setTimeout(() => {
      fitView({ padding: 0.2 });
    }, 100);
    
    return () => clearTimeout(timer);
  }, [initialNodes, initialEdges, setNodes, setEdges, fitView]);

  // Handle node click
  const onNodeClickHandler = useCallback(
    (_: React.MouseEvent, node: Node) => {
      onNodeClick?.(node.id);
    },
    [onNodeClick]
  ) as unknown as (event: React.MouseEvent, node: Node) => void;

  // Handle mouse move for tooltip
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (tooltip.visible) {
      setTooltip(prev => ({
        ...prev,
        x: e.clientX + 15,
        y: e.clientY - 10,
      }));
    }
  }, [tooltip.visible]);

  return (
    <FlowContainer className={className} onMouseMove={handleMouseMove}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClickHandler}
        nodeTypes={nodeTypes}
        fitView
        nodesDraggable={true}
        nodesConnectable={false}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#aaa" gap={16} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            switch (node.data.status) {
              case 'success':
                return '#198754';
              case 'running':
                return '#0d6efd';
              case 'failed':
                return '#dc3545';
              case 'retry':
                return '#fd7e14';
              case 'pending':
              default:
                return '#6c757d';
            }
          }}
          nodeStrokeWidth={3}
          zoomable
          pannable
        />
        <Panel position="top-right" className="bg-white p-2 rounded shadow-sm">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-medium">Status:</span>
            <StatusBadge status="success">Success</StatusBadge>
            <StatusBadge status="running">Running</StatusBadge>
            <StatusBadge status="failed">Failed</StatusBadge>
            <StatusBadge status="retry">Retry</StatusBadge>
            <StatusBadge status="pending">Pending</StatusBadge>
          </div>
        </Panel>
      </ReactFlow>
      
      {tooltip.visible && (
        <Tooltip
          style={{
            left: `${tooltip.x}px`,
            top: `${tooltip.y}px`,
            display: tooltip.visible ? 'block' : 'none',
          }}
        >
          {tooltip.content}
        </Tooltip>
      )}
    </FlowContainer>
  );
};

export const PlanDAGViewer: React.FC<PlanDAGViewerProps> = (props) => (
  <ReactFlowProvider>
    <PlanDAGViewerComponent {...props} />
  </ReactFlowProvider>
);