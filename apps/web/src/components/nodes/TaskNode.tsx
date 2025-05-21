import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import styled from '@emotion/styled';

// Styled components
const NodeContainer = styled.div<{ priority: string }>`
  padding: 12px;
  border-radius: 8px;
  background: white;
  border: 2px solid ${({ priority }) => {
    switch (priority.toLowerCase()) {
      case 'critical':
        return '#dc3545';
      case 'high':
        return '#fd7e14';
      case 'medium':
        return '#ffc107';
      case 'low':
        return '#20c997';
      default:
        return '#6c757d';
    }
  }};
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  min-width: 200px;
  max-width: 300px;
`;

const TaskHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
`;

const TaskId = styled.div`
  font-weight: bold;
  color: #495057;
`;

const AgentBadge = styled.div`
  background: #e9ecef;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.8em;
  color: #495057;
`;

const Description = styled.div`
  font-size: 0.9em;
  color: #6c757d;
  margin-bottom: 8px;
`;

const TaskDetails = styled.div`
  font-size: 0.8em;
  color: #6c757d;
`;

const DetailRow = styled.div`
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
`;

interface TaskNodeData {
  task_id: string;
  agent: string;
  description: string;
  priority: string;
  deadline?: string;
  max_retries?: number;
  fallback_agent?: string;
  timeout?: string;
  onClick?: () => void;
}

export const TaskNode = memo(({ data }: NodeProps<TaskNodeData>) => {
  const {
    task_id,
    agent,
    description,
    priority,
    deadline,
    max_retries,
    fallback_agent,
    timeout,
    onClick,
  } = data;

  return (
    <NodeContainer priority={priority} onClick={onClick}>
      <Handle type="target" position={Position.Top} />
      
      <TaskHeader>
        <TaskId>{task_id}</TaskId>
        <AgentBadge>{agent}</AgentBadge>
      </TaskHeader>
      
      <Description>{description}</Description>
      
      <TaskDetails>
        {deadline && (
          <DetailRow>
            <span>Deadline:</span>
            <span>{new Date(deadline).toLocaleString()}</span>
          </DetailRow>
        )}
        {max_retries !== undefined && (
          <DetailRow>
            <span>Max Retries:</span>
            <span>{max_retries}</span>
          </DetailRow>
        )}
        {fallback_agent && (
          <DetailRow>
            <span>Fallback:</span>
            <span>{fallback_agent}</span>
          </DetailRow>
        )}
        {timeout && (
          <DetailRow>
            <span>Timeout:</span>
            <span>{timeout}</span>
          </DetailRow>
        )}
      </TaskDetails>
      
      <Handle type="source" position={Position.Bottom} />
    </NodeContainer>
  );
}); 