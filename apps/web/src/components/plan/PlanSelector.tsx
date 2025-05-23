'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Upload } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PlanSelectorProps {
  onPlanSelect: (planId: string) => void;
  onUpload: (file: File) => void;
  selectedPlan?: string;
}

export function PlanSelector({ onPlanSelect, onUpload, selectedPlan }: PlanSelectorProps) {
  const [availablePlans, setAvailablePlans] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        // In a real implementation, this would be an API call
        // For now, we'll use a mock response
        const mockPlans = [
          'sample-plan-001',
          'test-plan-001',
          'retry-fallback-example',
          'live-test-plan'
        ];
        
        setAvailablePlans(mockPlans);
        // Select the first plan by default if none is selected
        if (!selectedPlan && mockPlans.length > 0) {
          onPlanSelect(mockPlans[0]);
        }
      } catch (err) {
        console.error('Failed to fetch plans:', err);
        setError('Failed to load available plans');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPlans();
  }, [onPlanSelect, selectedPlan]);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onUpload(file);
      // Reset the input to allow selecting the same file again
      event.target.value = '';
    }
  };

  const handlePlanChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onPlanSelect(e.target.value);
  };

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading plans...</div>;
  }

  if (error) {
    return <div className="text-sm text-destructive">{error}</div>;
  }

  return (
    <div className="flex flex-col space-y-4 w-full">
      <div className="flex items-center space-x-2">
        <div className="relative flex-1">
          <select
            value={selectedPlan || ''}
            onChange={handlePlanChange}
            disabled={availablePlans.length === 0}
            className={cn(
              'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background',
              'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
              'disabled:cursor-not-allowed disabled:opacity-50',
              'pr-10' // Add padding for the dropdown arrow
            )}
          >
            <option value="" disabled>
              Select a plan
            </option>
            {availablePlans.map((plan) => (
              <option key={plan} value={plan}>
                {plan}.yaml
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
            <svg
              className="h-4 w-4 text-muted-foreground"
              fill="none"
              height="24"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              width="24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="m7 15 5 5 5-5" />
              <path d="m7 9 5-5 5 5" />
            </svg>
          </div>
        </div>
        
        <input
          type="file"
          id="plan-upload"
          accept=".yaml,.yml"
          className="hidden"
          onChange={handleFileUpload}
        />
        <Button
          variant="outline"
          size="sm"
          className="whitespace-nowrap"
          onClick={() => document.getElementById('plan-upload')?.click()}
        >
          <Upload className="mr-2 h-4 w-4" />
          Upload
        </Button>
      </div>
      {availablePlans.length === 0 && (
        <div className="text-sm text-muted-foreground">
          No plans found. Upload a YAML plan to get started.
        </div>
      )}
    </div>
  );
}
