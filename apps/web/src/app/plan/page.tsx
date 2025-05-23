'use client';

import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ReactFlowProvider } from 'reactflow';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { PlanControlBar } from '@/components/plan/PlanControlBar';
import { PlanExecutionViewer } from '@/components/plan/PlanExecutionViewer';
import { DagViewer } from '@/components/plan/DagViewer';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, LayoutDashboard, Table2, Loader2, RefreshCw } from 'lucide-react';
import { getPlanExecution } from '@/api/executionApi';
import type { PlanExecution } from '@/types/execution';

interface PlanPageProps {
  params: {
    planId: string;
  };
}

export default function PlanPage() {
  const navigate = useNavigate();
  const routeParams = useParams();
  const [plan, setPlan] = useState<PlanExecution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedPlanId, setSelectedPlanId] = useState<string | undefined>(routeParams?.planId);
  const [activeView, setActiveView] = useState<'dag' | 'table'>('dag');


  const fetchPlan = async (id: string) => {
    try {
      setRefreshing(true);
      setError(null);
      const data = await getPlanExecution(id);
      setPlan(data);
    } catch (err) {
      console.error('Failed to fetch plan:', err);
      // Use mock data for demonstration
      if (id === 'sample-plan-001') {
        const mockPlan: PlanExecution = {
          plan_id: 'sample-plan-001',
          status: 'completed',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          tasks: [
            {
              task_id: 'VALIDATE_INPUT_DATA',
              agent: 'CA',
              type: 'data_processing',
              status: 'completed',
              score: 0.95,
              retry_count: 0,
              dependencies: []
            },
            {
              task_id: 'TRANSFORM_DATA',
              agent: 'CA',
              type: 'data_processing',
              status: 'completed',
              score: 0.92,
              retry_count: 0,
              dependencies: ['VALIDATE_INPUT_DATA']
            },
            {
              task_id: 'ASSESS_DATA_QUALITY',
              agent: 'CA',
              type: 'validation',
              status: 'completed',
              score: 0.88,
              retry_count: 0,
              dependencies: ['TRANSFORM_DATA']
            },
            {
              task_id: 'GENERATE_BUSINESS_REPORT',
              agent: 'WA',
              type: 'report_generation',
              status: 'in_progress',
              retry_count: 0,
              dependencies: ['TRANSFORM_DATA', 'ASSESS_DATA_QUALITY']
            },
            {
              task_id: 'SYSTEM_HEALTH_CHECK',
              agent: 'CC',
              type: 'health_check',
              status: 'completed',
              score: 1.0,
              retry_count: 0,
              dependencies: []
            },
            {
              task_id: 'ARCHIVE_AND_CLEANUP',
              agent: 'CC',
              type: 'custom',
              status: 'pending',
              retry_count: 0,
              dependencies: ['GENERATE_BUSINESS_REPORT']
            },
            {
              task_id: 'SEND_COMPLETION_NOTIFICATION',
              agent: 'WA',
              type: 'notification',
              status: 'pending',
              retry_count: 0,
              dependencies: ['GENERATE_BUSINESS_REPORT', 'ARCHIVE_AND_CLEANUP']
            }
          ]
        };
        setPlan(mockPlan);
        setError(null);
      } else {
        setError('Failed to load plan. Please try again.');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (selectedPlanId) {
      fetchPlan(selectedPlanId);
    } else {
      setLoading(false);
      setError('No plan selected');
    }
  }, [selectedPlanId]);

  const handleRefresh = () => {
    if (selectedPlanId) {
      fetchPlan(selectedPlanId);
    }
  };

  const handleActionComplete = () => {
    if (selectedPlanId) {
      fetchPlan(selectedPlanId);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Error state
  if (error && !plan) {
    return (
      <div className="container mx-auto p-4">
        <div className="flex flex-col items-center justify-center space-y-4 text-center">
          <Alert variant="destructive">
            <AlertTitle>Error Loading Plan</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <Button 
            variant="outline" 
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 md:p-6 space-y-6">
      <div className="flex flex-col space-y-4 mb-6">
        <div className="flex items-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(-1)}
            className="mr-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Refresh
          </Button>
          {plan && (
            <PlanControlBar 
              planId={plan.plan_id} 
              onActionComplete={handleActionComplete}
            />
          )}
        </div>
      </div>
      
      {plan && (
        <>
          <div className="grid gap-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">Plan Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Plan ID</p>
                    <p className="font-mono">{plan.plan_id}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Status</p>
                    <p className="capitalize">{plan.status.replace('_', ' ')}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Last Updated</p>
                    <p>{new Date(plan.updated_at).toLocaleString()}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="w-full">
              <div className="flex space-x-2 mb-4">
                <Button
                  variant={activeView === 'dag' ? 'default' : 'outline'}
                  onClick={() => setActiveView('dag')}
                  className="flex items-center"
                >
                  <LayoutDashboard className="h-4 w-4 mr-2" />
                  DAG View
                </Button>
                <Button
                  variant={activeView === 'table' ? 'default' : 'outline'}
                  onClick={() => setActiveView('table')}
                  className="flex items-center"
                >
                  <Table2 className="h-4 w-4 mr-2" />
                  Table View
                </Button>
              </div>
              
              {activeView === 'dag' && (
                <Card>
                  <CardHeader>
                    <CardTitle>Task Dependencies</CardTitle>
                    <CardDescription>
                      Visual representation of task dependencies and execution flow
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ReactFlowProvider>
                      <DagViewer 
                        tasks={plan.tasks} 
                        loading={loading}
                        error={error}
                        onRefresh={() => plan && fetchPlan(plan.plan_id)}
                      />
                    </ReactFlowProvider>
                  </CardContent>
                </Card>
              )}
              
              {activeView === 'table' && (
                <Card>
                  <CardHeader>
                    <CardTitle>Task Details</CardTitle>
                    <CardDescription>
                      Detailed view of all tasks in this plan ({plan.tasks.length} tasks)
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <PlanExecutionViewer 
                      tasks={plan.tasks} 
                      loading={loading}
                      error={error}
                      onRetry={() => plan && fetchPlan(plan.plan_id)}
                    />
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}