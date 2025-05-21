import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import styled from '@emotion/styled';
import { PlanDAGViewer } from '../components/PlanDAGViewer';

// Styled components
const PageContainer = styled.div`
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
`;

const Header = styled.div`
  margin-bottom: 24px;
`;

const Title = styled.h1`
  font-size: 24px;
  color: #212529;
  margin: 0 0 8px 0;
`;

const Description = styled.p`
  color: #6c757d;
  margin: 0;
`;

const PlanInfo = styled.div`
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const InfoGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
`;

const InfoItem = styled.div`
  display: flex;
  flex-direction: column;
`;

const InfoLabel = styled.span`
  font-size: 0.8em;
  color: #6c757d;
  margin-bottom: 4px;
`;

const InfoValue = styled.span`
  font-weight: 500;
  color: #212529;
`;

const VisualizationContainer = styled.div`
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  height: 600px;
`;

interface Plan {
  metadata: {
    plan_id: string;
    version: string;
    created?: string;
    description: string;
    priority: string;
    timeout?: string;
  };
  tasks: Array<{
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
  }>;
}

export const PlanView: React.FC = () => {
  const { planId } = useParams<{ planId: string }>();
  const [plan, setPlan] = useState<Plan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPlan = async () => {
      try {
        const response = await fetch(`/api/plans/${planId}`);
        if (!response.ok) {
          throw new Error('Failed to fetch plan');
        }
        const data = await response.json();
        setPlan(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchPlan();
  }, [planId]);

  const handleNodeClick = (taskId: string) => {
    // Handle task node click - could show task details in a modal
    console.log('Task clicked:', taskId);
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!plan) {
    return <div>Plan not found</div>;
  }

  return (
    <PageContainer>
      <Header>
        <Title>Plan: {plan.metadata.plan_id}</Title>
        <Description>{plan.metadata.description}</Description>
      </Header>

      <PlanInfo>
        <InfoGrid>
          <InfoItem>
            <InfoLabel>Version</InfoLabel>
            <InfoValue>{plan.metadata.version}</InfoValue>
          </InfoItem>
          <InfoItem>
            <InfoLabel>Priority</InfoLabel>
            <InfoValue>{plan.metadata.priority}</InfoValue>
          </InfoItem>
          <InfoItem>
            <InfoLabel>Created</InfoLabel>
            <InfoValue>
              {plan.metadata.created
                ? new Date(plan.metadata.created).toLocaleString()
                : 'N/A'}
            </InfoValue>
          </InfoItem>
          <InfoItem>
            <InfoLabel>Timeout</InfoLabel>
            <InfoValue>{plan.metadata.timeout || 'N/A'}</InfoValue>
          </InfoItem>
          <InfoItem>
            <InfoLabel>Tasks</InfoLabel>
            <InfoValue>{plan.tasks.length}</InfoValue>
          </InfoItem>
        </InfoGrid>
      </PlanInfo>

      <VisualizationContainer>
        <PlanDAGViewer plan={plan} onNodeClick={handleNodeClick} />
      </VisualizationContainer>
    </PageContainer>
  );
}; 