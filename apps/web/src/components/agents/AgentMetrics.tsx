import React from 'react';
import { Tooltip } from '../ui/tooltip';
import { Agent } from '../../types/agent';
import { 
  getScoreColor, 
  getScoreWidth, 
  getSuccessRateBadgeClass, 
  getTaskCountTooltip,
  generateDummyTrendData
} from '../../utils/metrics';
import { AreaChart, Area, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';

interface AgentMetricsProps {
  agent: Agent;
  className?: string;
}

const AgentMetrics: React.FC<AgentMetricsProps> = ({ agent, className = '' }) => {
  const { metrics = {} } = agent;
  const {
    averageScore = 0,
    successRate = 0,
    tasksCompleted = 0,
    tasksFailed = 0,
  } = metrics;

  const trendData = generateDummyTrendData();
  const totalTasks = tasksCompleted + tasksFailed;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Score Bar */}
      <div>
        <div className="flex justify-between text-sm mb-1">
          <span className="font-medium">Score</span>
          <span className="font-mono">{averageScore.toFixed(2)}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            className={`h-2.5 rounded-full ${getScoreColor(averageScore)}`}
            style={{ width: getScoreWidth(averageScore) }}
          />
        </div>
      </div>

      {/* Success Rate Badge */}
      <div>
        <span className={getSuccessRateBadgeClass(successRate)}>
          Success: {Math.round(successRate * 100)}%
        </span>
      </div>

      {/* Task Count with Tooltip */}
      <Tooltip content={getTaskCountTooltip(agent)}>
        <div className="text-sm text-gray-600 cursor-help">
          {totalTasks} tasks completed
        </div>
      </Tooltip>

      {/* Trend Chart */}
      {totalTasks > 0 && (
        <div className="h-24 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trendData} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#8884d8" stopOpacity={0.1}/>
                </linearGradient>
              </defs>
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 10 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                domain={[0, 1]} 
                hide={true}
              />
              <RechartsTooltip 
                formatter={(value: number) => [value.toFixed(2), 'Score']}
                labelFormatter={(label) => `Date: ${label}`}
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '0.375rem',
                  fontSize: '0.75rem',
                  padding: '0.25rem 0.5rem',
                }}
              />
              <Area 
                type="monotone" 
                dataKey="score" 
                stroke="#8884d8"
                fillOpacity={1} 
                fill="url(#scoreGradient)" 
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default AgentMetrics;
