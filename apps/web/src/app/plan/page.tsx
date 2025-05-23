'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { PlanControlBar } from '@/components/plan/PlanControlBar';
import { PlanExecutionViewer } from '@/components/plan/PlanExecutionViewer';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Loader2, RefreshCw } from 'lucide-react';
import { getPlanExecution } from '@/api/executionApi';
import type { PlanExecution } from '@/api/executionApi';

interface PlanPageParams {
  planId: string;
}

export default function PlanPage() {
  const router = useRouter();
  const { planId } = router.query as unknown as PlanPageParams;
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [plan, setPlan] = useState<PlanExecution | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Check if planId is available
  useEffect(() => {
    if (!planId) {
      setError('No plan ID provided');
      setLoading(false);
    }
  }, [planId]);

  const fetchPlan = async (id: string) => {
    try {
      setLoading(true);
      const data = await getPlanExecution(id);
      setPlan(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching plan:', err);
      setError('Failed to load plan execution data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchPlan(planId);
  };

  const handleActionComplete = (action: string) => {
    console.log(`Action ${action} completed`);
    // Refresh the plan data after an action
    fetchPlan(planId);
  };

  useEffect(() => {
    if (planId) {
      fetchPlan(planId);
    }
  }, [planId]);

  if (loading && !refreshing) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <div className="bg-destructive/10 border border-destructive text-destructive p-4 rounded-lg">
          <p className="font-medium">Error loading plan</p>
          <p className="text-sm mt-1">{error}</p>
          <div className="mt-4 space-x-2">
            <Button 
              variant="outline" 
              onClick={() => router.back()}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Go Back
            </Button>
            {planId && (
              <Button 
                variant="outline" 
                onClick={() => fetchPlan(planId)}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Retry
              </Button>
            )}
          </div>
        </div>
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
      
      {plan ? (
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

            <PlanExecutionViewer 
              tasks={plan.tasks} 
              className="w-full"
              loading={loading}
              error={error}
              onRetry={() => fetchPlan(plan.plan_id)}
            />
          </div>
        </>
      ) : (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">No plan data available</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}