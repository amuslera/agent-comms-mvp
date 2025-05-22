import type { NodeProps } from 'reactflow';
import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
// @ts-ignore - We'll install @emotion/styled later
import styled from '@emotion/styled';

// Styled components
const NodeContainer = styled.div<{ priority: string; status?: string }>`
  padding: 12px;
  border-radius: 8px;
  background: white;
  border: 2px solid ${({ priority, status }: { priority: string; status?: string }) => {
    // Border color based on status first, then priority
    if (status) {
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
          return '#6c757d';
      }
    }
    
    // Fall back to priority if no status
    switch (priority?.toLowerCase()) {
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 220px;
  max-width: 300px;
  transition: all 0.2s ease;
  cursor: pointer;
  overflow: hidden;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
`;

const StatusIndicator = styled.div<{ status?: string }>`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: ${({ status }: { status?: string }) => {
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
`;

const TaskHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
  position: relative;
  padding-top: 4px;
`;

const TaskId = styled.div`
  font-weight: 600;
  color: #212529;
  font-size: 0.95em;
  margin-right: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const AgentBadge = styled.div`
  background: #e9ecef;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75em;
  color: #495057;
  font-weight: 500;
  white-space: nowrap;
`;

const Description = styled.div`
  font-size: 0.85em;
  color: #495057;
  margin: 8px 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const TaskDetails = styled.div`
  font-size: 0.75em;
  color: #6c757d;
  border-top: 1px solid #e9ecef;
  padding-top: 8px;
  margin-top: 8px;
`;

const DetailRow = styled.div<{ highlight?: boolean }>`
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-weight: ${({ highlight }: { highlight?: boolean }) => (highlight ? '600' : 'normal')};
  color: ${({ highlight }: { highlight?: boolean }) => (highlight ? '#212529' : 'inherit')};
`;

const StatusBadge = styled.span<{ status?: string }>`
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.7em;
  font-weight: 600;
  text-transform: capitalize;
  background-color: ${({ status }: { status?: string }) => {
    switch (status) {
      case 'success':
        return '#19875420';
      case 'running':
        return '#0d6efd20';
      case 'failed':
        return '#dc354520';
      case 'retry':
        return '#fd7e1420';
      case 'pending':
      default:
        return '#6c757d20';
    }
  }};
  color: ${({ status }: { status?: string }) => {
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
`;

interface TaskNodeData {
  task_id: string;
  agent: string;
  type: string;
  description: string;
  priority: string;
  status?: 'pending' | 'running' | 'success' | 'failed' | 'retry';
  duration_sec?: number;
  score?: number;
  onClick?: () => void;
  onMouseEnter?: (e: React.MouseEvent, node: { id: string }) => void;
  onMouseLeave?: () => void;
}

export const TaskNode = memo(({ data }: NodeProps<TaskNodeData>) => {
  const {
    task_id,
    agent,
    description,
    priority,
    status,
    duration_sec,
    score,
    onClick,
    onMouseEnter,
    onMouseLeave,
  } = data;

  // Format duration for display
  const formatDuration = (seconds?: number) => {
    if (seconds === undefined) return 'N/A';
    if (seconds < 1) return '<1s';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  // Format score as percentage
  const formatScore = (scoreValue?: number) => {
    if (scoreValue === undefined) return 'N/A';
    return `${(scoreValue * 100).toFixed(1)}%`;
  };

  return (
    <NodeContainer 
      priority={priority} 
      status={status}
      onClick={onClick}
      onMouseEnter={(e: React.MouseEvent) => onMouseEnter?.(e, { id: task_id })}
      onMouseLeave={onMouseLeave}
    >
      <StatusIndicator status={status} />
      <Handle type="target" position={Position.Top} />
      
      <TaskHeader>
        <TaskId title={task_id}>{task_id}</TaskId>
        <AgentBadge title={`Agent: ${agent}`}>
          {agent}
        </AgentBadge>
      </TaskHeader>
      
      <Description title={description}>
        {description}
      </Description>
      
      <TaskDetails>
        <DetailRow>
          <span>Status:</span>
          <StatusBadge status={status}>
            {status || 'pending'}
          </StatusBadge>
        </DetailRow>
        
        <DetailRow>
          <span>Duration:</span>
          <span>{formatDuration(duration_sec)}</span>
        </DetailRow>
        
        {score !== undefined && (
          <DetailRow highlight={score !== undefined && score < 0.6}>
            <span>Score:</span>
            <span>{formatScore(score)}</span>
          </DetailRow>
        )}
      </TaskDetails>
      
      <Handle type="source" position={Position.Bottom} />
    </NodeContainer>
  );
});