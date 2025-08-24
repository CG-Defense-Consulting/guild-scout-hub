import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useUpdateQueueStatus, useDeleteFromQueue } from '@/hooks/use-database';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/use-auth';
import { Calendar, Package, Eye, ArrowRight, ArrowLeft, Trash2, ExternalLink, FileText, Database } from 'lucide-react';
import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { getClosedStatusDotColor } from '@/lib/utils';

interface KanbanBoardProps {
  columns: string[];
  contracts: any[];
  getContractsByStatus: (status: string) => any[];
  onContractClick: (contract: any) => void;
  loading: boolean;
}

// RFQ PDF Button Component for Kanban Board
const RfqPdfButton = ({ solicitationNumber, contractId }: { solicitationNumber: string; contractId: string }) => {
  const [hasPdf, setHasPdf] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  // Check if RFQ PDF exists in Supabase
  useEffect(() => {
    // Reset state when solicitation number or contract ID changes
    setHasPdf(false);
    setPdfUrl(null);
    
    const checkForRfqPdf = async () => {
      try {
        // Search for files with contract-{contractId}- prefix
        const { data: files, error } = await supabase.storage
          .from('docs')
          .list('', {
            search: `contract-${contractId}-`
          });

        if (error) {
          console.error('Error checking for RFQ PDF:', error);
          return;
        }

        if (files && files.length > 0) {
          // Look for files that contain the solicitation number
          // Check for both .PDF and .pdf extensions
          const rfqFile = files.find(file => 
            file.name.includes(solicitationNumber) && 
            (file.name.toLowerCase().endsWith('.pdf'))
          );
          
          if (rfqFile) {
            // Create a signed URL for the PDF
            const { data: urlData, error: urlError } = await supabase.storage
              .from('docs')
              .createSignedUrl(rfqFile.name, 86400); // 24 hour expiry for better UX

            if (urlError) {
              console.error('Error creating signed URL:', urlError);
              return;
            }

            setHasPdf(true);
            setPdfUrl(urlData.signedUrl);
          }
        }
      } catch (error) {
        console.error('Error checking for RFQ PDF:', error);
      }
    };

    checkForRfqPdf();
  }, [solicitationNumber, contractId]);

  const handleClick = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click
    if (hasPdf && pdfUrl) {
      // Open the PDF from Supabase
      window.open(pdfUrl, '_blank');
    } else {
      // Fallback to direct DIBBS link
      const lastChar = solicitationNumber.slice(-1);
      const dibbsUrl = `https://dibbs2.bsm.dla.mil/Downloads/RFQ/${lastChar}/${solicitationNumber}.PDF`;
      window.open(dibbsUrl, '_blank');
    }
  };

  return (
    <Button
      size="sm"
      variant="ghost"
      className={`h-6 w-6 p-0 flex-shrink-0 ${
        hasPdf 
          ? 'text-green-600 hover:text-green-700 hover:bg-green-50' 
          : 'text-blue-600 hover:text-blue-700 hover:bg-blue-50'
      }`}
      onClick={handleClick}
      title={hasPdf ? `View RFQ PDF from Supabase (${solicitationNumber})` : `View RFQ PDF from DIBBS (${solicitationNumber})`}
    >
      <FileText className="w-3 h-3" />
    </Button>
  );
};

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
    
    // Handle card click to view details
    const handleCardClick = (e: React.MouseEvent) => {
      // Don't trigger if clicking on buttons or their children
      const target = e.target as HTMLElement;
      if (target.closest('button')) {
        return;
      }
      onContractClick(contract);
    };
    
    return (
      <Card className="mb-3 cursor-pointer hover:shadow-md transition-shadow" onClick={handleCardClick}>
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
                
                {/* Workflow Needed Indicator */}
                {!contract.cde_g && (
                  <div className="group relative">
                    <Badge 
                      variant="outline" 
                      className="text-xs text-yellow-600 border-yellow-300 bg-yellow-50 cursor-help"
                      title="This contract needs the NSN AMSC workflow to extract the AMSC code from DIBBS. Click the contract to view details and run the workflow."
                    >
                      Missing AMSC Code
                    </Badge>
                  </div>
                )}
                
                {/* AMSC Status Indicator */}
                {contract.cde_g && (
                  <div className="flex items-center gap-1">
                    <div className={`w-2 h-2 rounded-full ${contract.cde_g === 'G' ? 'bg-green-500' : 'bg-blue-500'}`} />
                    <span className="text-xs text-muted-foreground">
                      AMSC: {contract.cde_g}
                    </span>
                  </div>
                )}
                
                {/* Closed Status Indicator */}
                {contract.closed === true && (
                  <div className="flex items-center gap-1">
                    <div className={`w-2 h-2 rounded-full ${getClosedStatusDotColor(contract.closed, contract.current_stage)}`} />
                    <span className="text-xs text-muted-foreground">
                      Closed
                    </span>
                  </div>
                )}
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
                  <RfqPdfButton 
                    key={`rfq-${contract.solicitation_number}-${contract.id}`}
                    solicitationNumber={contract.solicitation_number}
                    contractId={contract.id}
                  />
                )}
                
                {/* Tech Doc Link */}
                {contract.solicitation_number && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-6 w-6 p-0 flex-shrink-0 text-green-600 hover:text-green-700 hover:bg-green-50"
                    onClick={(e) => {
                      e.stopPropagation(); // Prevent card click
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
                    onClick={(e) => {
                      e.stopPropagation(); // Prevent card click
                      const url = `https://www.dibbs.bsm.dla.mil/RFQ/RFQNsn.aspx?value=${contract.national_stock_number}&category=nsn`;
                      window.open(url, '_blank');
                    }}
                    title="View NSN Details"
                  >
                    <Database className="w-3 h-3" />
                  </Button>
                )}
                
                {/* Delete button */}
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 w-6 p-0 flex-shrink-0 text-red-500 hover:text-red-700 hover:bg-red-50"
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent card click
                    handleDeleteContract(contract.id, contract.solicitation_number);
                  }}
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
                      onClick={(e) => {
                        e.stopPropagation(); // Prevent card click
                        handleStatusChange(contract.id, targetStatus);
                      }}
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
                      onClick={(e) => {
                        e.stopPropagation(); // Prevent card click
                        handleStatusChange(contract.id, targetStatus);
                      }}
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