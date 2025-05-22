import React, { useCallback, useMemo } from 'react';
import ReactFlow, {
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  ReactFlowProvider,
} from 'reactflow';
import type { Node, Edge, Connection } from 'reactflow';
import 'reactflow/dist/style.css';

export interface PlanTask {
  task_id: string;
  agent_id: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'retry';
  score?: number;
  description?: string;
  dependencies?: string[];
}

interface PlanDAGViewerProps {
  tasks?: PlanTask[];
}

const TaskNode = ({ data }: { data: PlanTask }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 border-green-500 text-green-800';
      case 'failed':
        return 'bg-red-100 border-red-500 text-red-800';
      case 'retry':
        return 'bg-yellow-100 border-yellow-500 text-yellow-800';
      case 'running':
        return 'bg-blue-100 border-blue-500 text-blue-800';
      default:
        return 'bg-gray-100 border-gray-500 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return '✅';
      case 'failed':
        return '❌';
      case 'retry':
        return '🔄';
      case 'running':
        return '⏳';
      default:
        return '⏸️';
    }
  };

  return (
    <div 
      className={`px-4 py-2 border-2 rounded-lg shadow-md min-w-32 ${getStatusColor(data.status)}`}
      title={`Agent: ${data.agent_id}, Score: ${data.score || 'N/A'}, Status: ${data.status}`}
    >
      <div className="flex items-center gap-2">
        <span className="text-lg">{getStatusIcon(data.status)}</span>
        <div>
          <div className="font-semibold text-sm">{data.task_id}</div>
          <div className="text-xs opacity-75">{data.agent_id}</div>
        </div>
      </div>
    </div>
  );
};

const nodeTypes = {
  taskNode: TaskNode,
};

const PlanDAGViewerInternal: React.FC<PlanDAGViewerProps> = ({ tasks = [] }) => {
  // Mock data if no tasks provided
  const mockTasks: PlanTask[] = useMemo(() => [
    { task_id: 'task-001', agent_id: 'ARCH', status: 'success', score: 95, dependencies: [] },
    { task_id: 'task-002', agent_id: 'CA', status: 'running', score: 85, dependencies: ['task-001'] },
    { task_id: 'task-003', agent_id: 'CC', status: 'failed', score: 45, dependencies: ['task-001'] },
    { task_id: 'task-004', agent_id: 'WA', status: 'retry', score: 70, dependencies: ['task-002', 'task-003'] },
    { task_id: 'task-005', agent_id: 'ARCH', status: 'pending', dependencies: ['task-004'] },
  ], []);

  const taskData = tasks.length > 0 ? tasks : mockTasks;

  const initialNodes: Node[] = useMemo(() => {
    return taskData.map((task, index) => ({
      id: task.task_id,
      type: 'taskNode',
      position: { x: (index % 3) * 200, y: Math.floor(index / 3) * 100 },
      data: task,
    }));
  }, [taskData]);

  const initialEdges: Edge[] = useMemo(() => {
    const edges: Edge[] = [];
    taskData.forEach(task => {
      if (task.dependencies) {
        task.dependencies.forEach(depId => {
          edges.push({
            id: `${depId}-${task.task_id}`,
            source: depId,
            target: task.task_id,
            type: 'smoothstep',
            animated: task.status === 'running',
          });
        });
      }
    });
    return edges;
  }, [taskData]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <div className="w-full h-96 border border-gray-300 rounded-lg">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        className="bg-gray-50"
      >
        <Controls />
        <MiniMap />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>
    </div>
  );
};

const PlanDAGViewer: React.FC<PlanDAGViewerProps> = (props) => {
  return (
    <ReactFlowProvider>
      <PlanDAGViewerInternal {...props} />
    </ReactFlowProvider>
  );
};

export default PlanDAGViewer;