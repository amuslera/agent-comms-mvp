import { Plan } from '../pages/PlanView';

export const mockPlan: Plan = {
  metadata: {
    plan_id: 'plan-123',
    version: '1.0.0',
    created: '2025-05-21T10:00:00Z',
    description: 'Example plan for testing the DAG viewer',
    priority: 'high',
    timeout: '1h'
  },
  tasks: [
    {
      task_id: 'task-1',
      agent: 'ARCH',
      type: 'planning',
      description: 'Initial planning phase',
      priority: 'high',
      content: {},
      dependencies: [],
      status: 'success',
      duration_sec: 12.34,
      score: 0.95
    },
    {
      task_id: 'task-2',
      agent: 'CA',
      type: 'execution',
      description: 'Code analysis',
      priority: 'high',
      content: {},
      dependencies: ['task-1'],
      status: 'success',
      duration_sec: 45.67,
      score: 0.88
    },
    {
      task_id: 'task-3',
      agent: 'WA',
      type: 'execution',
      description: 'Web application updates',
      priority: 'medium',
      content: {},
      dependencies: ['task-1'],
      status: 'running',
      duration_sec: 23.45,
      score: 0.0
    },
    {
      task_id: 'task-4',
      agent: 'QA',
      type: 'verification',
      description: 'Quality assurance',
      priority: 'high',
      content: {},
      dependencies: ['task-2', 'task-3'],
      status: 'pending',
      duration_sec: 0,
      score: 0.0
    },
    {
      task_id: 'task-5',
      agent: 'ARCH',
      type: 'review',
      description: 'Final review',
      priority: 'critical',
      content: {},
      dependencies: ['task-4'],
      status: 'pending',
      duration_sec: 0,
      score: 0.0
    }
  ]
};

export const mockGraphData = {
  nodes: mockPlan.tasks.map(task => ({
    id: task.task_id,
    type: 'task',
    data: {
      ...task,
      label: task.task_id,
      onClick: () => console.log(`Task clicked: ${task.task_id}`)
    },
    position: { x: 0, y: 0 } // Will be calculated by layout
  })),
  edges: mockPlan.tasks.flatMap(task =>
    task.dependencies.map(depId => ({
      id: `${depId}-${task.task_id}`,
      source: depId,
      target: task.task_id,
      type: 'smoothstep',
      animated: true
    }))
  )
};
