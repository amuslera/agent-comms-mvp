import React from 'react';
import PlanDAGViewer from '../../components/PlanDAGViewer';

const PlanPage: React.FC = () => {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Plan DAG Viewer</h1>
      <p className="mb-4">Testing DAG viewer component:</p>
      <div className="bg-white rounded-lg shadow-lg p-6" style={{ minHeight: '500px' }}>
        <PlanDAGViewer />
      </div>
    </div>
  );
};

export default PlanPage;