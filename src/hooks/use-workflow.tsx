import { useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

interface WorkflowTriggerParams {
  workflow_name: string;
  contract_id?: string;
  nsn?: string;
  solicitation_number?: string;
  target_date?: string;
  verbose?: boolean;
}

interface WorkflowResponse {
  success: boolean;
  message: string;
  workflow: string;
  workflow_file: string;
  params: Record<string, any>;
  triggered_at: string;
}

export const useWorkflow = () => {
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const triggerWorkflow = async (params: WorkflowTriggerParams): Promise<WorkflowResponse | null> => {
    setIsLoading(true);
    
    try {
      // Call the Supabase Edge Function
      const { data, error } = await supabase.functions.invoke('trigger-workflow', {
        body: params
      });

      if (error) {
        console.error('Edge function error:', error);
        toast({
          title: 'Workflow Trigger Failed',
          description: error.message || 'Failed to trigger workflow',
          variant: 'destructive',
        });
        return null;
      }

      if (data?.success) {
        toast({
          title: 'Workflow Triggered',
          description: data.message || 'Workflow started successfully',
        });
        return data as WorkflowResponse;
      } else {
        toast({
          title: 'Workflow Trigger Failed',
          description: data?.error || 'Unknown error occurred',
          variant: 'destructive',
        });
        return null;
      }

    } catch (error) {
      console.error('Workflow trigger error:', error);
      toast({
        title: 'Workflow Trigger Failed',
        description: 'Network error occurred while triggering workflow',
        variant: 'destructive',
      });
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  // Convenience methods for specific workflows
  const triggerPullSingleRfqPdf = (solicitation_number: string) => {
    return triggerWorkflow({
      workflow_name: 'pull_single_rfq_pdf',
      solicitation_number
    });
  };

  const triggerExtractNsnAmsc = (contract_id: string, nsn: string, verbose?: boolean) => {
    return triggerWorkflow({
      workflow_name: 'extract_nsn_amsc',
      contract_id,
      nsn,
      verbose
    });
  };

  const triggerPullDayRfqPdfs = (target_date: string) => {
    return triggerWorkflow({
      workflow_name: 'pull_day_rfq_pdfs',
      target_date
    });
  };

  const triggerPullDayRfqIndexExtract = (target_date: string) => {
    return triggerWorkflow({
      workflow_name: 'pull_day_rfq_index_extract',
      target_date
    });
  };

  const triggerPullSingleAwardHistory = (solicitation_number: string) => {
    return triggerWorkflow({
      workflow_name: 'pull_single_award_history',
      solicitation_number
    });
  };

  const triggerPullDayAwardHistory = (target_date: string) => {
    return triggerWorkflow({
      workflow_name: 'pull_day_award_history',
      target_date
    });
  };

  return {
    isLoading,
    triggerWorkflow,
    triggerPullSingleRfqPdf,
    triggerExtractNsnAmsc,
    triggerPullDayRfqPdfs,
    triggerPullDayRfqIndexExtract,
    triggerPullSingleAwardHistory,
    triggerPullDayAwardHistory,
  };
};
