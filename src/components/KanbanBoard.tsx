import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useUpdateQueueStatus, useDeleteFromQueue } from '@/hooks/use-database';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/use-auth';
import { Calendar, Package, Eye, ArrowRight, ArrowLeft, Trash2, ExternalLink, FileText, Database } from 'lucide-react';

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
  const { user } = useAuth();
  const updateStatus = useUpdateQueueStatus();
  const deleteFromQueue = useDeleteFromQueue();

  // Define stage transition rules
  const stageTransitions: Record<string, { forward: string[], backward: string[] }> = {
    'Analysis': {
      forward: ['Sent to Partner', 'Pricing', 'Bid Submitted'],
      backward: []
    },
    'Sent to Partner': {
      forward: ['Pricing', 'Bid Submitted'],
      backward: ['Analysis']
    },
    'Pricing': {
      forward: ['Bid Submitted'],
      backward: ['Analysis', 'Sent to Partner']
    },
    'Bid Submitted': {
      forward: ['Awarded'],
      backward: ['Analysis', 'Sent to Partner', 'Pricing']
    },
    'Awarded': {
      forward: ['Production'],
      backward: ['Bid Submitted']
    },
    'Production': {
      forward: ['Delivered'],
      backward: ['Awarded']
    },
    'Delivered': {
      forward: ['Paid'],
      backward: ['Production']
    },
    'Paid': {
      forward: [],
      backward: ['Delivered']
    }
  };

  // Get valid transitions for a contract's current stage
  const getValidTransitions = (currentStage: string) => {
    const transitions = stageTransitions[currentStage] || { forward: [], backward: [] };
    return {
      forward: transitions.forward,
      backward: transitions.backward,
      all: [...transitions.forward, ...transitions.backward]
    };
  };

  const handleStatusChange = async (contractId: string, newStatus: string) => {
    try {
      await updateStatus.mutateAsync({ 
        id: contractId, 
        status: newStatus, 
        userId: user?.id 
      });
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

  const handleDeleteContract = async (contractId: string, solicitationNumber: string) => {
    // Use a more user-friendly confirmation dialog
    const contractIdentifier = solicitationNumber || contractId;
    const isConfirmed = window.confirm(
      `Are you sure you want to delete contract "${contractIdentifier}"?\n\n` +
      `This action will:\n` +
      `• Remove the contract from the queue\n` +
      `• Delete all associated timeline data\n` +
      `• Cannot be undone\n\n` +
      `Click OK to confirm deletion.`
    );
    
    if (!isConfirmed) {
      return;
    }

    try {
      await deleteFromQueue.mutateAsync(contractId);
      toast({
        title: 'Contract Deleted',
        description: `Contract "${contractIdentifier}" has been removed from the queue`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete contract. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const ContractCard = ({ contract, currentColumn }: { contract: any; currentColumn: string }) => {
    const currentStage = contract.current_stage || currentColumn;
    const validTransitions = getValidTransitions(currentStage);
    
    return (
      <Card className="mb-3 cursor-pointer hover:shadow-md transition-shadow">
        <CardContent className="p-3">
          <div className="flex gap-3">
            {/* Left side - Contract details */}
            <div className="flex-1 space-y-2 min-w-0">
              <div className="space-y-1">
                <Badge variant="secondary" className="font-mono text-xs">
                  {contract.solicitation_number || 'No Solicitation #'}
                </Badge>
                <div className="text-xs text-muted-foreground font-mono">
                  {contract.national_stock_number || 'No NSN'}
                </div>
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
            
            {/* Right side - Stage transitions and view button */}
            <div className="flex flex-col items-end gap-2 min-w-0">
              {/* Action buttons row - all inline */}
              <div className="flex gap-1">
                {/* RFQ PDF Link */}
                {contract.solicitation_number && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-6 w-6 p-0 flex-shrink-0 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                    onClick={() => {
                      const lastChar = contract.solicitation_number.slice(-1);
                      const url = `https://dibbs2.bsm.dla.mil/Downloads/RFQ/${lastChar}/${contract.solicitation_number}.PDF`;
                      window.open(url, '_blank');
                    }}
                    title="View RFQ PDF"
                  >
                    <FileText className="w-3 h-3" />
                  </Button>
                )}
                
                {/* Tech Doc Link */}
                {contract.solicitation_number && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-6 w-6 p-0 flex-shrink-0 text-green-600 hover:text-green-700 hover:bg-green-50"
                    onClick={() => {
                      const url = `https://pcf1x.bsm.dla.mil/cfolders/fol_de.htm?p_sol_no=${contract.solicitation_number}`;
                      window.open(url, '_blank');
                    }}
                    title="View Technical Documentation"
                  >
                    <ExternalLink className="w-3 h-3" />
                  </Button>
                )}
                
                {/* NSN Detail Link */}
                {contract.national_stock_number && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-6 w-6 p-0 flex-shrink-0 text-purple-600 hover:text-purple-700 hover:bg-purple-50"
                    onClick={() => {
                      const url = `https://www.dibbs.bsm.dla.mil/RFQ/RFQNsn.aspx?value=${contract.national_stock_number}&category=nsn`;
                      window.open(url, '_blank');
                    }}
                    title="View NSN Details"
                  >
                    <Database className="w-3 h-3" />
                  </Button>
                )}
                
                {/* View button */}
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 w-6 p-0 flex-shrink-0"
                  onClick={() => onContractClick(contract)}
                >
                  <Eye className="w-3 h-3" />
                </Button>
                
                {/* Delete button */}
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 w-6 p-0 flex-shrink-0 text-red-500 hover:text-red-700 hover:bg-red-50"
                  onClick={() => handleDeleteContract(contract.id, contract.solicitation_number)}
                  disabled={deleteFromQueue.isPending}
                >
                  <Trash2 className="w-3 h-3" />
                </Button>
              </div>
              
              {/* Stage transition buttons */}
              {validTransitions.all.length > 0 && (
                <div className="flex flex-col gap-1 min-w-0">
                  {/* Forward transitions */}
                  {validTransitions.forward.map((targetStatus) => (
                    <Button
                      key={`forward-${targetStatus}`}
                      size="sm"
                      variant="ghost"
                      className="h-5 px-2 text-xs justify-start text-green-600 hover:text-green-700 hover:bg-green-50 border border-transparent hover:border-green-200 min-w-0"
                      onClick={() => handleStatusChange(contract.id, targetStatus)}
                      disabled={updateStatus.isPending}
                    >
                      <ArrowRight className="w-3 h-3 mr-1 flex-shrink-0" />
                      <span className="truncate">{targetStatus}</span>
                    </Button>
                  ))}
                  
                  {/* Backward transitions */}
                  {validTransitions.backward.map((targetStatus) => (
                    <Button
                      key={`backward-${targetStatus}`}
                      size="sm"
                      variant="ghost"
                      className="h-5 px-2 text-xs justify-start text-orange-600 hover:text-orange-700 hover:bg-orange-50 border border-transparent hover:border-orange-200 min-w-0"
                      onClick={() => handleStatusChange(contract.id, targetStatus)}
                      disabled={updateStatus.isPending}
                    >
                      <ArrowLeft className="w-3 h-3 mr-1 flex-shrink-0" />
                      <span className="truncate">{targetStatus}</span>
                    </Button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

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
              <CardHeader className="py-3 px-4">
                <CardTitle className="text-sm font-medium flex items-center justify-between h-6">
                  <span className="flex items-center">{columnName}</span>
                  <Badge variant="outline" className="ml-2 flex-shrink-0">
                    {columnContracts.length}
                  </Badge>
                </CardTitle>
              </CardHeader>
            </Card>
            
            <div className="space-y-2 min-h-[200px]">
              {columnContracts.map((contract) => (
                <ContractCard 
                  key={contract.id} 
                  contract={contract} 
                  currentColumn={columnName}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};