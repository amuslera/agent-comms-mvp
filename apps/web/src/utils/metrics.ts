import { Agent } from '../types/agent';

export const getScoreColor = (score: number): string => {
  if (score >= 0.9) return 'bg-green-100 text-green-800';
  if (score >= 0.7) return 'bg-yellow-100 text-yellow-800';
  return 'bg-red-100 text-red-800';
};

export const getScoreWidth = (score: number): string => {
  return `${Math.round(score * 100)}%`;
};

export const getSuccessRateBadgeClass = (successRate: number): string => {
  if (successRate >= 0.9) return 'bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded';
  if (successRate >= 0.75) return 'bg-yellow-100 text-yellow-800 text-xs font-medium px-2.5 py-0.5 rounded';
  return 'bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded';
};

export const generateDummyTrendData = (): { date: string; score: number }[] => {
  const baseDate = new Date();
  return Array.from({ length: 7 }, (_, i) => {
    const date = new Date(baseDate);
    date.setDate(date.getDate() - (6 - i));
    return {
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      score: 0.7 + Math.random() * 0.3, // Random score between 0.7 and 1.0
    };
  });
};

export const getTaskCountTooltip = (agent: Agent): string => {
  const { tasksCompleted = 0, tasksFailed = 0 } = agent.metrics || {};
  const totalTasks = tasksCompleted + tasksFailed;
  const successRate = tasksCompleted / (totalTasks || 1);
  
  return `${totalTasks} tasks (${Math.round(successRate * 100)}% success rate)`;
};
