import React, { useCallback } from 'react';
import PlanDAGViewer from '../../components/PlanDAGViewer';
import { PlanControlBar } from '../../components/plan/PlanControlBar';
// This would typically come from your router params or state management
const MOCK_PLAN_ID = 'plan-123';

const PlanPage: React.FC = () => {
  const handleActionComplete = useCallback((action: string) => {
    console.log(`Action ${action} completed`);
    // You can add additional logic here after an action completes
  }, []);

  return (
    <div className="container mx-auto p-4 md:p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Plan Execution</h1>
        <p className="text-gray-600">View and manage the execution plan</p>
      </div>
      
      {/* Plan Control Bar */}
      <div className="bg-white rounded-lg shadow-sm border">
        <PlanControlBar 
          planId={MOCK_PLAN_ID} 
          onActionComplete={handleActionComplete}
          className="border-b rounded-t-lg"
        />
        
        {/* DAG Viewer */}
        <div className="p-4 bg-gray-50 rounded-b-lg" style={{ minHeight: '600px' }}>
          <PlanDAGViewer />
        </div>
      </div>
      
      {/* Plan Details Section - Optional */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <h2 className="text-lg font-semibold mb-3">Plan Details</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-500">Plan ID</p>
            <p className="font-mono text-sm">{MOCK_PLAN_ID}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Status</p>
            <p className="text-sm">Running</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Created</p>
            <p className="text-sm">{new Date().toLocaleString()}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlanPage;