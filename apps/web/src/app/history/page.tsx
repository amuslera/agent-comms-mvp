import React, { useEffect, useState } from 'react';
import { getPlanHistory, PlanHistoryItem } from '../../api/planApi';
import { getRecentTasks, RecentTask } from '../../api/taskApi';
import Drawer from '../../components/ui/Drawer';

const PAGE_SIZE = 10;

export default function HistoryPage() {
  // State for plans
  const [plans, setPlans] = useState<PlanHistoryItem[]>([]);
  const [plansCount, setPlansCount] = useState(0);
  const [plansLoading, setPlansLoading] = useState(true);
  const [plansError, setPlansError] = useState<string | null>(null);
  const [plansPage, setPlansPage] = useState(0);

  // State for tasks
  const [tasks, setTasks] = useState<RecentTask[]>([]);
  const [tasksCount, setTasksCount] = useState(0);
  const [tasksLoading, setTasksLoading] = useState(true);
  const [tasksError, setTasksError] = useState<string | null>(null);
  const [tasksPage, setTasksPage] = useState(0);

  // Drawer state
  const [selectedTask, setSelectedTask] = useState<RecentTask | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Fetch plans
  useEffect(() => {
    setPlansLoading(true);
    setPlansError(null);
    getPlanHistory({ limit: PAGE_SIZE, offset: plansPage * PAGE_SIZE })
      .then((data) => {
        setPlans(data.plans);
        setPlansCount(data.count);
      })
      .catch((err) => setPlansError(err.message || 'Failed to load plan history'))
      .finally(() => setPlansLoading(false));
  }, [plansPage]);

  // Fetch tasks
  useEffect(() => {
    setTasksLoading(true);
    setTasksError(null);
    getRecentTasks({ limit: PAGE_SIZE, offset: tasksPage * PAGE_SIZE })
      .then((data) => {
        setTasks(data.tasks);
        setTasksCount(data.count);
      })
      .catch((err) => setTasksError(err.message || 'Failed to load recent tasks'))
      .finally(() => setTasksLoading(false));
  }, [tasksPage]);

  // Handler to open drawer
  const handleTaskClick = (task: RecentTask) => {
    setSelectedTask(task);
    setDrawerOpen(true);
  };

  // Handler to close drawer
  const handleDrawerClose = () => {
    setDrawerOpen(false);
    setTimeout(() => setSelectedTask(null), 200); // Wait for animation
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Plan & Task History</h1>
      {/* Plans Table */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-2">Plans</h2>
        <div className="bg-white shadow rounded-lg overflow-x-auto">
          {plansLoading ? (
            <div className="p-6 text-center text-gray-500">Loading plans...</div>
          ) : plansError ? (
            <div className="p-6 text-center text-red-500">{plansError}</div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Plan ID</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Submitted At</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Agent Count</th>
                  <th className="px-4 py-2"></th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {plans.map((plan) => (
                  <tr key={plan.plan_id} className="hover:bg-gray-50 transition">
                    <td className="px-4 py-2 font-mono text-sm">{plan.plan_id}</td>
                    <td className="px-4 py-2 text-sm">{new Date(plan.submitted_at).toLocaleString()}</td>
                    <td className="px-4 py-2 text-sm">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${plan.status === 'completed' ? 'bg-green-100 text-green-700' : plan.status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'}`}>{plan.status}</span>
                    </td>
                    <td className="px-4 py-2 text-sm text-center">{plan.agent_count}</td>
                    <td className="px-4 py-2 text-right">
                      {/* Expandable row stub */}
                      <button className="text-blue-500 hover:underline text-xs" disabled>Details</button>
                    </td>
                  </tr>
                ))}
                {plans.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-gray-400">No plans found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
        {/* Pagination */}
        <div className="flex justify-end items-center mt-2 gap-2">
          <button
            className="px-3 py-1 rounded bg-gray-200 text-gray-700 disabled:opacity-50"
            onClick={() => setPlansPage((p) => Math.max(0, p - 1))}
            disabled={plansPage === 0}
          >
            Prev
          </button>
          <span className="text-sm">Page {plansPage + 1}</span>
          <button
            className="px-3 py-1 rounded bg-gray-200 text-gray-700 disabled:opacity-50"
            onClick={() => setPlansPage((p) => ((p + 1) * PAGE_SIZE < plansCount ? p + 1 : p))}
            disabled={(plansPage + 1) * PAGE_SIZE >= plansCount}
          >
            Next
          </button>
        </div>
      </section>

      {/* Tasks Table */}
      <section>
        <h2 className="text-xl font-semibold mb-2">Recent Tasks</h2>
        <div className="bg-white shadow rounded-lg overflow-x-auto">
          {tasksLoading ? (
            <div className="p-6 text-center text-gray-500">Loading tasks...</div>
          ) : tasksError ? (
            <div className="p-6 text-center text-red-500">{tasksError}</div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Trace ID</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Agent</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Retry Count</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Success</th>
                  <th className="px-4 py-2"></th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {tasks.map((task) => (
                  <tr
                    key={task.trace_id}
                    className="hover:bg-gray-50 transition cursor-pointer"
                    onClick={() => handleTaskClick(task)}
                  >
                    <td className="px-4 py-2 font-mono text-sm">{task.trace_id}</td>
                    <td className="px-4 py-2 text-sm">{task.agent}</td>
                    <td className="px-4 py-2 text-sm">{task.score != null ? task.score.toFixed(2) : '-'}</td>
                    <td className="px-4 py-2 text-sm text-center">{task.retry_count}</td>
                    <td className="px-4 py-2 text-sm">
                      {task.success ? (
                        <span className="px-2 py-1 rounded text-xs font-semibold bg-green-100 text-green-700">Yes</span>
                      ) : (
                        <span className="px-2 py-1 rounded text-xs font-semibold bg-red-100 text-red-700">No</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-right">
                      {/* Expandable row stub */}
                      <button className="text-blue-500 hover:underline text-xs" disabled>Details</button>
                    </td>
                  </tr>
                ))}
                {tasks.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-6 text-center text-gray-400">No tasks found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
        {/* Pagination */}
        <div className="flex justify-end items-center mt-2 gap-2">
          <button
            className="px-3 py-1 rounded bg-gray-200 text-gray-700 disabled:opacity-50"
            onClick={() => setTasksPage((p) => Math.max(0, p - 1))}
            disabled={tasksPage === 0}
          >
            Prev
          </button>
          <span className="text-sm">Page {tasksPage + 1}</span>
          <button
            className="px-3 py-1 rounded bg-gray-200 text-gray-700 disabled:opacity-50"
            onClick={() => setTasksPage((p) => ((p + 1) * PAGE_SIZE < tasksCount ? p + 1 : p))}}
            disabled={(tasksPage + 1) * PAGE_SIZE >= tasksCount}
          >
            Next
          </button>
        </div>
        {/* Task Detail Drawer */}
        <Drawer open={drawerOpen} onClose={handleDrawerClose} title="Task Details">
          {selectedTask ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2">
                <div className="text-gray-500 text-xs">Trace ID</div>
                <div className="font-mono text-xs break-all">{selectedTask.trace_id || 'N/A'}</div>
                <div className="text-gray-500 text-xs">Agent</div>
                <div>{selectedTask.agent || 'N/A'}</div>
                <div className="text-gray-500 text-xs">Status</div>
                <div>{selectedTask.success === true ? 'Success' : selectedTask.success === false ? 'Failed' : 'N/A'}</div>
                <div className="text-gray-500 text-xs">Score</div>
                <div>{selectedTask.score != null ? selectedTask.score.toFixed(2) : 'N/A'}</div>
                <div className="text-gray-500 text-xs">Duration (sec)</div>
                <div>{selectedTask.duration_sec != null ? selectedTask.duration_sec : 'N/A'}</div>
                <div className="text-gray-500 text-xs">Retry Count</div>
                <div>{selectedTask.retry_count != null ? selectedTask.retry_count : 'N/A'}</div>
              </div>
              <div>
                <div className="text-gray-500 text-xs mb-1">Input Payload</div>
                <pre className="bg-gray-100 rounded p-2 text-xs overflow-x-auto">{JSON.stringify(selectedTask.input_payload || {}, null, 2)}</pre>
              </div>
              <div>
                <div className="text-gray-500 text-xs mb-1">Output Payload</div>
                <pre className="bg-gray-100 rounded p-2 text-xs overflow-x-auto">{JSON.stringify(selectedTask.output_payload || {}, null, 2)}</pre>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-gray-500 text-xs">Submitted</div>
                <div>{selectedTask.submitted_at ? new Date(selectedTask.submitted_at).toLocaleString() : 'N/A'}</div>
                <div className="text-gray-500 text-xs">Started</div>
                <div>{selectedTask.started_at ? new Date(selectedTask.started_at).toLocaleString() : 'N/A'}</div>
                <div className="text-gray-500 text-xs">Completed</div>
                <div>{selectedTask.completed_at ? new Date(selectedTask.completed_at).toLocaleString() : 'N/A'}</div>
              </div>
              <div>
                <div className="text-gray-500 text-xs mb-1">Retry History</div>
                <div className="text-xs text-gray-400 italic">(stub) Retry history coming soon.</div>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-400">No task selected.</div>
          )}
        </Drawer>
      </section>
    </div>
  );
} 