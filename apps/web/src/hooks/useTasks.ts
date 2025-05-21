import { useState, useEffect } from 'react';
import { Task, getTasks } from '../api/taskApi';

interface UseTasksResult {
  tasks: Task[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  taskCounts: {
    pending: number;
    in_progress: number;
    completed: number;
    failed: number;
    cancelled: number;
  };
}

interface UseTasksOptions {
  limit?: number;
  status?: string;
  agentId?: string;
}

/**
 * Custom hook to fetch and manage tasks data
 * @param options Options for filtering and pagination
 * @returns Object containing tasks, loading state, error, refresh function, and task counts
 */
export const useTasks = (options: UseTasksOptions = {}): UseTasksResult => {
  const { limit, status, agentId } = options;
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [taskCounts, setTaskCounts] = useState({
    pending: 0,
    in_progress: 0,
    completed: 0,
    failed: 0,
    cancelled: 0,
  });

  const fetchTasks = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getTasks({ limit, status, agent_id: agentId });
      setTasks(data.tasks);
      
      // Calculate task counts
      const counts = {
        pending: 0,
        in_progress: 0,
        completed: 0,
        failed: 0,
        cancelled: 0,
      };
      
      data.tasks.forEach((task) => {
        if (task.status in counts) {
          counts[task.status as keyof typeof counts]++;
        }
      });
      
      setTaskCounts(counts);
    } catch (err) {
      setError('Failed to fetch tasks. Please try again later.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchTasks();
    
    // Set up polling every 10 seconds
    const intervalId = setInterval(fetchTasks, 10000);
    
    // Clean up interval on unmount
    return () => clearInterval(intervalId);
  }, [limit, status, agentId]);

  return {
    tasks,
    loading,
    error,
    refresh: fetchTasks,
    taskCounts,
  };
};
