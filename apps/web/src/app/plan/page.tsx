'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { PlanControlBar } from '@/components/plan/PlanControlBar';
import { PlanExecutionViewer } from '@/components/plan/PlanExecutionViewer';
import { DagViewer } from '@/components/plan/DagViewer';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, LayoutDashboard, Table2, Loader2, RefreshCw } from 'lucide-react';
import { getPlanExecution } from '@/api/executionApi';
import type { PlanExecution } from '@/types/execution';

interface PlanPageProps {
  params: {
    planId: string;
  };
}

export default function PlanPage({ params }: PlanPageProps) {
  const router = useRouter();
  const [plan, setPlan] = useState<PlanExecution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const planId = params?.planId;

  const fetchPlan = async (id: string) => {
    try {
      setRefreshing(true);
      setError(null);
      const data = await getPlanExecution(id);
      setPlan(data);
    } catch (err) {
      console.error('Failed to fetch plan:', err);
      setError('Failed to load plan. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (planId) {
      fetchPlan(planId);
    } else {
      setLoading(false);
      setError('No plan ID provided');
    }
  }, [planId]);

  const handleRefresh = () => {
    if (planId) {
      fetchPlan(planId);
    }
  };

  const handleActionComplete = () => {
    if (planId) {
      fetchPlan(planId);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading plan...</span>
      </div>
    );
  }

  if (!planId) {
    return (
      <div className="p-4 text-center">
        <p className="text-muted-foreground">No plan ID provided</p>
        <Button 
          variant="outline" 
          className="mt-4"
          onClick={() => router.back()}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Go back
        </Button>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center">
        <p className="text-destructive">{error}</p>
        <Button 
          variant="outline" 
          className="mt-4"
          onClick={() => planId && fetchPlan(planId)}
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 md:p-6 space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-foreground">Plan Execution</h1>
          <p className="text-muted-foreground">
            {plan?.plan_id || 'Viewing plan execution details'}
          </p>
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

            <Tabs defaultValue="dag" className="w-full">
              <TabsList className="grid w-full max-w-md grid-cols-2">
                <TabsTrigger value="dag">
                  <LayoutDashboard className="h-4 w-4 mr-2" />
                  DAG View
                </TabsTrigger>
                <TabsTrigger value="table">
                  <Table2 className="h-4 w-4 mr-2" />
                  Table View
                </TabsTrigger>
              </TabsList>
              <TabsContent value="dag" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Task Dependencies</CardTitle>
                    <CardDescription>
                      Visual representation of task dependencies and execution flow
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <DagViewer 
                      tasks={plan.tasks} 
                      loading={loading}
                      error={error}
                      onRefresh={() => plan && fetchPlan(plan.plan_id)}
                    />
                  </CardContent>
                </Card>
              </TabsContent>
              <TabsContent value="table" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Task Details</CardTitle>
                    <CardDescription>
                      Detailed view of all tasks in this plan
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
              </TabsContent>
            </Tabs>
          </div>
        </>
      )}
    </div>
  );
}