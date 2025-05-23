'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { PlanControlBar } from '@/components/plan/PlanControlBar';
import { PlanExecutionViewer } from '@/components/plan/PlanExecutionViewer';
import { DagViewer } from '@/components/plan/DagViewer';
import { PlanSelector } from '@/components/plan/PlanSelector';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Loader2, RefreshCw, LayoutDashboard, Table2, ArrowLeft } from 'lucide-react';
import { getPlanExecution } from '@/api/executionApi';
import { parseYamlFile } from '@/utils/yamlUtils';
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
  const [selectedPlanId, setSelectedPlanId] = useState<string | undefined>(params?.planId);

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

  const handlePlanSelect = (planId: string) => {
    setSelectedPlanId(planId);
    // In a real implementation, we would update the URL and load the selected plan
    // router.push(`/plan/${planId}`);
  };

  const handlePlanUpload = async (file: File) => {
    try {
      setLoading(true);
      const uploadedPlan = await parseYamlFile(file);
      // In a real implementation, we would use the parsed plan
      console.log('Uploaded plan:', uploadedPlan);
      setSelectedPlanId(`uploaded-${Date.now()}`);
      setError(null);
    } catch (err) {
      console.error('Failed to process uploaded file:', err);
      setError('Failed to process uploaded file. Please check the format and try again.');
    } finally {
      setLoading(false);
    }
  };

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

  useEffect(() => {
    if (selectedPlanId) {
      fetchPlan(selectedPlanId);
    } else {
      setLoading(false);
    }
  }, [selectedPlanId]);

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Error state
  if (error) {
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

  // Plan selection state
  if (!selectedPlanId) {
    return (
      <div className="container mx-auto p-4">
        <div className="flex flex-col space-y-4">
          <div className="flex items-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.back()}
              className="mr-4"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <h1 className="text-2xl font-bold">Plan Execution</h1>
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Select a Plan</CardTitle>
              <CardDescription>Choose an existing plan or upload a new one to get started</CardDescription>
            </CardHeader>
            <CardContent>
              <PlanSelector 
                onPlanSelect={handlePlanSelect}
                onUpload={handlePlanUpload}
                selectedPlan={selectedPlanId}
              />
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Main content when a plan is selected
  return (
    <div className="container mx-auto p-4 space-y-6">
      {/* Header with back button and title */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.back()}
            className="mr-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <h1 className="text-2xl font-bold">Plan Execution</h1>
        </div>
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
      </div>

      {/* Plan selector */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle>Selected Plan</CardTitle>
          <CardDescription>View and manage the current plan</CardDescription>
        </CardHeader>
        <CardContent>
          <PlanSelector 
            onPlanSelect={handlePlanSelect}
            onUpload={handlePlanUpload}
            selectedPlan={selectedPlanId}
          />
        </CardContent>
      </Card>

      {plan ? (
        <>
          {/* Plan info */}
          <Card>
            <CardHeader>
              <CardTitle>Plan Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Plan ID</p>
                  <p className="font-mono text-sm">{plan.plan_id}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Status</p>
                  <p className="capitalize">{plan.status?.replace('_', ' ')}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Last Updated</p>
                  <p>{plan.updated_at ? new Date(plan.updated_at).toLocaleString() : 'N/A'}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tabs for DAG and Table views */}
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
                    tasks={plan.tasks || []} 
                    loading={loading}
                    error={error}
                    onRefresh={handleRefresh}
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
                    tasks={plan.tasks || []} 
                    loading={loading}
                    error={error}
                    onRetry={handleRefresh}
                  />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Plan control bar */}
          <div className="flex justify-end">
            <PlanControlBar 
              planId={plan.plan_id} 
              onActionComplete={handleActionComplete}
            />
          </div>
        </>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>No Plan Data</CardTitle>
            <CardDescription>Unable to load plan data. Please try again.</CardDescription>
          </CardHeader>
          <CardContent>
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
          </CardContent>
        </Card>
      )}
    </div>
  );
}
