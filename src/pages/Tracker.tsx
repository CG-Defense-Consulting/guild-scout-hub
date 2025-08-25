import { useState } from 'react';
import { KanbanBoard } from '@/components/KanbanBoard';
import { ContractDetail } from '@/components/ContractDetail';
import { useContractQueue } from '@/hooks/use-database';
import { Badge } from '@/components/ui/badge';
import { BarChart3, Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useWorkflow } from '@/hooks/use-workflow';
import { useToast } from '@/hooks/use-toast';

export const Tracker = () => {
  const { data: contracts = [], isLoading } = useContractQueue();
  const [selectedContract, setSelectedContract] = useState<any>(null);
  const { triggerUniversalContractQueueWorkflowDirect, isLoading: isWorkflowLoading } = useWorkflow();
  const { toast } = useToast();

  const lifecycleColumns = [
    'Analysis',
    'Sent to Partner',
    'Pricing',
    'Bid Submitted',
    'Awarded',
    'Production',
    'Delivered',
    'Paid'
  ];

  const getContractsByStatus = (status: string) => {
    return contracts.filter(contract => 
              contract.current_stage === status
    );
  };

  const handleDispatchWorkflow = async () => {
    try {
      const result = await triggerUniversalContractQueueWorkflowDirect();
      if (result) {
        toast({
          title: 'Workflow Dispatched',
          description: 'Universal contract queue workflow has been triggered successfully.',
        });
      }
    } catch (error) {
      console.error('Failed to dispatch workflow:', error);
      toast({
        title: 'Workflow Dispatch Failed',
        description: 'Failed to trigger the universal contract queue workflow.',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-guild-brand-fg flex items-center gap-2">
            <BarChart3 className="w-6 h-6" />
            Contract Tracker
          </h1>
          <p className="text-muted-foreground">Manage contract lifecycle and progress</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            onClick={handleDispatchWorkflow}
            size="sm"
            variant="outline"
            className="flex items-center gap-2"
            disabled={isWorkflowLoading}
          >
            <Play className="w-4 h-4" />
            {isWorkflowLoading ? 'Dispatching...' : 'Dispatch Workflow'}
          </Button>
          <Badge variant="outline" className="bg-guild-accent-1/10 text-guild-accent-1">
            {contracts.length} active contracts
          </Badge>
        </div>
      </div>

      <KanbanBoard
        columns={lifecycleColumns}
        contracts={contracts}
        getContractsByStatus={getContractsByStatus}
        onContractClick={setSelectedContract}
        loading={isLoading}
      />

      <ContractDetail
        contract={selectedContract}
        open={!!selectedContract}
        onOpenChange={(open) => !open && setSelectedContract(null)}
      />
    </div>
  );
};

export default Tracker;