import { Button } from '@/components/ui/button';
import { Loader2, RefreshCw, AlertTriangle, X } from 'lucide-react';
import { useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../../api/config';
import toast from 'react-hot-toast';

interface PlanControlBarProps {
  planId: string;
  onActionComplete?: (action: string) => void;
  className?: string;
}

type ActionType = 'resubmit' | 'escalate' | 'cancel';

const actionConfig = {
  resubmit: {
    label: 'Resubmit Plan',
    icon: <RefreshCw className="mr-2 h-4 w-4" />,
    endpoint: (id: string) => `${API_BASE_URL}/plans/${id}/resubmit`,
    successMessage: 'Plan resubmitted successfully',
    errorMessage: 'Failed to resubmit plan',
    variant: 'default' as const,
  },
  escalate: {
    label: 'Escalate Plan',
    icon: <AlertTriangle className="mr-2 h-4 w-4" />,
    endpoint: (id: string) => `${API_BASE_URL}/plans/${id}/escalate`,
    successMessage: 'Plan escalated successfully',
    errorMessage: 'Failed to escalate plan',
    variant: 'outline' as const,
  },
  cancel: {
    label: 'Cancel Plan',
    icon: <X className="mr-2 h-4 w-4" />,
    endpoint: (id: string) => `${API_BASE_URL}/plans/${id}/cancel`,
    successMessage: 'Plan cancelled successfully',
    errorMessage: 'Failed to cancel plan',
    variant: 'destructive' as const,
  },
};

export function PlanControlBar({
  planId,
  onActionComplete,
  className = '',
}: PlanControlBarProps) {
  const [loading, setLoading] = useState<ActionType | null>(null);

  const handleAction = async (action: ActionType) => {
    const config = actionConfig[action];
    setLoading(action);
    
    try {
      // This is a mock API call - replace with actual implementation
      await axios.post(config.endpoint(planId), {}, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      toast.success(config.successMessage);
      
      onActionComplete?.(action);
    } catch (error) {
      console.error(`${config.errorMessage}:`, error);
      
      toast.error(config.errorMessage);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className={`flex flex-wrap gap-2 p-4 bg-card border rounded-lg ${className}`}>
      {(Object.keys(actionConfig) as ActionType[]).map((action) => {
        const config = actionConfig[action];
        const isLoading = loading === action;
        
        return (
          <Button
            key={action}
            variant={config.variant}
            onClick={() => handleAction(action)}
            disabled={!!loading}
            className="min-w-[150px] justify-center"
          >
            {isLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              config.icon
            )}
            {config.label}
          </Button>
        );
      })}
    </div>
  );
}

export default PlanControlBar;
