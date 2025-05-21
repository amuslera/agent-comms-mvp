import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Textarea } from '../components/ui/textarea';
import { useToast } from '../components/ui/use-toast';
import { submitPlan } from '../api/planApi';

export default function PlanSubmission() {
  const [planContent, setPlanContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState<{
    success: boolean;
    message: string;
    planId?: string;
  } | null>(null);
  
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!planContent.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a plan before submitting',
        variant: 'destructive',
      });
      return;
    }

    setIsSubmitting(true);
    setSubmissionResult(null);

    try {
      const result = await submitPlan(planContent);
      setSubmissionResult({
        success: true,
        message: 'Plan submitted successfully!',
        planId: result.plan_id,
      });
      
      toast({
        title: 'Success',
        description: 'Plan submitted successfully!',
      });
      
      // Clear the form after successful submission
      setPlanContent('');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to submit plan';
      setSubmissionResult({
        success: false,
        message: errorMessage,
      });
      
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto py-8">
      <Card className="max-w-3xl mx-auto">
        <CardHeader>
          <CardTitle>Submit a New Plan</CardTitle>
          <CardDescription>
            Enter your task plan in YAML or JSON format. The plan will be submitted to the backend for processing.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Textarea
                id="plan-content"
                value={planContent}
                onChange={(e) => setPlanContent(e.target.value)}
                placeholder={
                  'Enter plan in YAML or JSON format. Example:\n\n' +
                  'name: Example Plan\n' +
                  'description: A sample plan for demonstration\n' +
                  'tasks:\n' +
                  '  - id: task1\n' +
                  '    type: sample_task\n' +
                  '    params:\n' +
                  '      param1: value1\n' +
                  '      param2: value2'
                }
                className="min-h-[300px] font-mono text-sm"
                disabled={isSubmitting}
              />
            </div>
            
            <div className="flex justify-end space-x-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/')}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Submitting...' : 'Submit Plan'}
              </Button>
            </div>
          </form>

          {submissionResult && (
            <div className={`mt-6 p-4 rounded-md ${
              submissionResult.success 
                ? 'bg-green-50 text-green-800 border border-green-200' 
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}>
              <h3 className="font-medium">
                {submissionResult.success ? '✅ Success' : '❌ Error'}
              </h3>
              <p className="mt-1">{submissionResult.message}</p>
              {submissionResult.planId && (
                <div className="mt-2 p-2 bg-white rounded border border-gray-200">
                  <span className="font-medium">Plan ID:</span>{' '}
                  <code className="bg-gray-100 px-2 py-1 rounded text-sm">
                    {submissionResult.planId}
                  </code>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
