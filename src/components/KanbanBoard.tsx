import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useUpdateQueueStatus } from '@/hooks/use-database';
import { useToast } from '@/hooks/use-toast';
import { Calendar, Package, Eye } from 'lucide-react';

interface KanbanBoardProps {
  columns: string[];
  contracts: any[];
  getContractsByStatus: (status: string) => any[];
  onContractClick: (contract: any) => void;
  loading: boolean;
}

export const KanbanBoard = ({ 
  columns, 
  contracts, 
  getContractsByStatus, 
  onContractClick,
  loading 
}: KanbanBoardProps) => {
  const { toast } = useToast();
  const updateStatus = useUpdateQueueStatus();

  const handleStatusChange = async (contractId: string, newStatus: string) => {
    try {
      await updateStatus.mutateAsync({ id: contractId, status: newStatus });
      toast({
        title: 'Status Updated',
        description: `Contract moved to ${newStatus}`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update contract status',
        variant: 'destructive',
      });
    }
  };

  const ContractCard = ({ contract }: { contract: any }) => (
    <Card className="mb-3 cursor-pointer hover:shadow-md transition-shadow">
      <CardContent className="p-3">
        <div className="space-y-2">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <Badge variant="secondary" className="font-mono text-xs">
                {contract.solicitation_number || 'No Solicitation #'}
              </Badge>
              <div className="text-xs text-muted-foreground font-mono">
                {contract.national_stock_number || 'No NSN'}
              </div>
            </div>
            <Button
              size="sm"
              variant="ghost"
              className="h-6 w-6 p-0"
              onClick={() => onContractClick(contract)}
            >
              <Eye className="w-3 h-3" />
            </Button>
          </div>
          
          <p className="text-sm text-foreground font-medium line-clamp-2">
            {contract.description || 'No description'}
          </p>
          
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {contract.quote_issue_date || 'No date'}
            </div>
            <div className="flex items-center gap-1">
              <Package className="w-3 h-3" />
              {contract.quantity ? contract.quantity.toLocaleString() : 'No quantity'}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-guild-accent-1 mx-auto"></div>
        <p className="mt-2 text-muted-foreground">Loading contracts...</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {columns.map((columnName) => {
        const columnContracts = getContractsByStatus(columnName);
        
        return (
          <div key={columnName} className="space-y-3">
            <Card className="bg-guild-brand-bg/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium flex items-center justify-between">
                  {columnName}
                  <Badge variant="outline" className="ml-2">
                    {columnContracts.length}
                  </Badge>
                </CardTitle>
              </CardHeader>
            </Card>
            
            <div className="space-y-2 min-h-[200px]">
              {columnContracts.map((contract) => (
                <div key={contract.id}>
                  <ContractCard contract={contract} />
                  
                  {/* Quick status change buttons */}
                  <div className="flex gap-1 px-2 pb-2">
                    {columns.map((targetStatus) => {
                      if (targetStatus === columnName) return null;
                      
                      return (
                        <Button
                          key={targetStatus}
                          size="sm"
                          variant="ghost"
                          className="h-6 px-2 text-xs"
                          onClick={() => handleStatusChange(contract.id, targetStatus)}
                          disabled={updateStatus.isPending}
                        >
                          → {targetStatus}
                        </Button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};