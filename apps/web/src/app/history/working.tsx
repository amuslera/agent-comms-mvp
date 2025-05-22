import React, { useEffect, useState } from 'react';

interface PlanItem {
  plan_id: string;
  submitted_at: string;
  status: string;
  agent_count: number;
}

interface TaskItem {
  trace_id: string;
  agent: string;
  score?: number;
  retry_count: number;
  success: boolean;
}

export default function WorkingHistory() {
  const [plans, setPlans] = useState<PlanItem[]>([]);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch plans
        const plansResponse = await fetch('http://localhost:8000/plans/history?limit=10');
        const plansData = await plansResponse.json();
        
        // Fetch tasks
        const tasksResponse = await fetch('http://localhost:8000/tasks/recent?limit=10');
        const tasksData = await tasksResponse.json();
        
        setPlans(plansData.plans || []);
        setTasks(tasksData.tasks || []);
        setError(null);
      } catch (err) {
        setError(`Failed to load data: ${err}`);
        console.error('Error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Plan & Task History</h1>
        <div className="text-center py-8">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Plan & Task History</h1>
        <div className="text-center py-8 text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Plan & Task History</h1>
      
      {/* Plans Section */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4">Plans ({plans.length})</h2>
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Plan ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Submitted</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Agents</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {plans.map((plan) => (
                <tr key={plan.plan_id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">{plan.plan_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(plan.submitted_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      plan.status === 'complete' 
                        ? 'bg-green-100 text-green-800' 
                        : plan.status === 'failed'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {plan.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{plan.agent_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Tasks Section */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Recent Tasks ({tasks.length})</h2>
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trace ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Agent</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Retries</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Success</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tasks.map((task) => (
                <tr key={task.trace_id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">{task.trace_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{task.agent}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {task.score ? task.score.toFixed(2) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{task.retry_count}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      task.success 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {task.success ? 'Yes' : 'No'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}