import { useState } from 'react';
import { KanbanBoard } from '@/components/KanbanBoard';
import { ContractDetail } from '@/components/ContractDetail';
import { useContractQueue } from '@/hooks/use-database';
import { Badge } from '@/components/ui/badge';
import { BarChart3 } from 'lucide-react';

export const Tracker = () => {
  const { data: contracts = [], isLoading } = useContractQueue();
  const [selectedContract, setSelectedContract] = useState<any>(null);

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