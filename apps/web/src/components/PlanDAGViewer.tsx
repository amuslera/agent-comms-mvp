import React, { useCallback, useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  NodeTypes as ReactFlowNodeTypes,
  useNodesState,
  useEdgesState,
} from 'reactflow';
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
  deadline?: string;
  content: Record<string, any>;
  dependencies: string[];
  max_retries?: number;
  fallback_agent?: string;
  timeout?: string;
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

interface Plan {
  metadata: PlanMetadata;
  tasks: PlanTask[];
}

// Styled components
const FlowContainer = styled.div`
  width: 100%;
  height: 100%;
  min-height: 500px;
  background: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
`;

const nodeTypes: ReactFlowNodeTypes = {
  task: TaskNode,
};

interface PlanDAGViewerProps {
  plan: Plan;
  onNodeClick?: (taskId: string) => void;
}

export const PlanDAGViewer: React.FC<PlanDAGViewerProps> = ({ plan, onNodeClick }) => {
  // Convert plan tasks to nodes and edges
  const { initialNodes, initialEdges } = useMemo(() => {
    const nodes: Node[] = plan.tasks.map((task, index) => ({
      id: task.task_id,
      type: 'task',
      position: { x: 0, y: index * 150 }, // Initial positions, will be adjusted by layout
      data: {
        ...task,
        onClick: () => onNodeClick?.(task.task_id),
      },
    }));

    const edges: Edge[] = plan.tasks.flatMap((task) =>
      task.dependencies.map((depId) => ({
        id: `${depId}-${task.task_id}`,
        source: depId,
        target: task.task_id,
        type: 'smoothstep',
        animated: true,
      }))
    );

    return { initialNodes: nodes, initialEdges: edges };
  }, [plan, onNodeClick]);

  // State for nodes and edges
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Handle node click
  const onNodeClickHandler = useCallback(
    (_: React.MouseEvent, node: Node) => {
      onNodeClick?.(node.id);
    },
    [onNodeClick]
  );

  return (
    <FlowContainer>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClickHandler}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </FlowContainer>
  );
}; 