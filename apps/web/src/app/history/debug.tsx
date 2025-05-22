import React, { useEffect, useState } from 'react';

export default function HistoryDebug() {
  const [status, setStatus] = useState('Starting...');
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    setStatus('Making API calls...');
    
    // Test plan history
    fetch('http://localhost:8000/plans/history?limit=3')
      .then(response => response.json())
      .then(planData => {
        setStatus('Plan API successful');
        
        // Test tasks API
        return fetch('http://localhost:8000/tasks/recent?limit=3');
      })
      .then(response => response.json())
      .then(taskData => {
        setStatus('Both APIs successful');
        setData({ plans: taskData, tasks: taskData });
      })
      .catch(error => {
        setStatus(`Error: ${error.message}`);
        console.error('API Error:', error);
      });
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">History Debug Page</h1>
      <div className="mb-4">
        <strong>Status:</strong> {status}
      </div>
      {data && (
        <div>
          <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}