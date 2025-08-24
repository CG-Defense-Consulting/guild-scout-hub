import { useState, useEffect, useCallback, useRef } from 'react';
import { useContractQueue } from './use-database';
import { useWorkflow } from './use-workflow';
import { useToast } from './use-toast';
import { supabase } from '@/integrations/supabase/client';

interface ContractWatcherConfig {
  enabled?: boolean;
  checkInterval?: number; // milliseconds
  maxConcurrentWorkflows?: number;
  autoTrigger?: boolean;
}

interface WorkflowQueueItem {
  contractId: string;
  solicitationNumber: string;
  nsn: string;
  type: 'rfq_pdf' | 'nsn_amsc';
  timestamp: Date;
  status: 'pending' | 'running' | 'completed' | 'failed';
}

export const useContractWatcher = (config: ContractWatcherConfig = {}) => {
  const {
    enabled = true,
    checkInterval = 30000, // 30 seconds
    maxConcurrentWorkflows = 3,
    autoTrigger = true
  } = config;

  const { data: contracts = [] } = useContractQueue();
  const { triggerPullSingleRfqPdf, triggerExtractNsnAmsc } = useWorkflow();
  const { toast } = useToast();
  
  const [workflowQueue, setWorkflowQueue] = useState<WorkflowQueueItem[]>([]);
  const [isWatching, setIsWatching] = useState(false);
  const [stats, setStats] = useState({
    totalContracts: 0,
    contractsWithoutAmsc: 0,
    workflowsTriggered: 0,
    workflowsCompleted: 0,
    workflowsFailed: 0
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const runningWorkflowsRef = useRef<Set<string>>(new Set());

  // Find contracts that need workflow processing
  const findContractsNeedingWorkflows = useCallback(() => {
    const contractsWithoutAmsc = contracts.filter(contract => {
      // Check if contract has no AMSC code
      const hasNoAmsc = !contract.cde_g;
      
      // Check if contract is not already in the workflow queue
      const notInQueue = !workflowQueue.some(item => 
        item.contractId === contract.id && 
        (item.type === 'nsn_amsc' || item.type === 'rfq_pdf')
      );
      
      // Check if contract has required data
      const hasRequiredData = contract.solicitation_number && contract.national_stock_number;
      
      return hasNoAmsc && notInQueue && hasRequiredData;
    });

    return contractsWithoutAmsc;
  }, [contracts, workflowQueue]);

  // Add contract to workflow queue
  const addToWorkflowQueue = useCallback((contract: any, type: 'rfq_pdf' | 'nsn_amsc') => {
    const queueItem: WorkflowQueueItem = {
      contractId: contract.id,
      solicitationNumber: contract.solicitation_number,
      nsn: contract.national_stock_number,
      type,
      timestamp: new Date(),
      status: 'pending'
    };

    setWorkflowQueue(prev => [...prev, queueItem]);
    
    toast({
      title: 'Workflow Queued',
      description: `${type === 'rfq_pdf' ? 'RFQ PDF' : 'NSN AMSC'} workflow queued for ${contract.solicitation_number}`,
    });
  }, [toast]);

  // Check for contracts needing workflows and queue them
  const checkAndQueueContracts = useCallback(() => {
    if (!enabled || !autoTrigger) return;

    const contractsNeedingWorkflows = findContractsNeedingWorkflows();
    
    if (contractsNeedingWorkflows.length === 0) return;

    // Queue RFQ PDF workflow first for contracts without AMSC codes
    for (const contract of contractsNeedingWorkflows) {
      // Check if we already have an RFQ PDF workflow queued for this contract
      const hasRfqWorkflow = workflowQueue.some(item => 
        item.contractId === contract.id && item.type === 'rfq_pdf'
      );

      if (!hasRfqWorkflow) {
        addToWorkflowQueue(contract, 'rfq_pdf');
      }
    }

    // Update stats
    setStats(prev => ({
      ...prev,
      totalContracts: contracts.length,
      contractsWithoutAmsc: contractsNeedingWorkflows.length
    }));
  }, [enabled, autoTrigger, findContractsNeedingWorkflows, workflowQueue, contracts.length, addToWorkflowQueue]);

  // Check if we should queue NSN AMSC workflow after RFQ PDF completion
  const checkForNsnAmscWorkflow = useCallback((completedContractId: string) => {
    const contract = contracts.find(c => c.id === completedContractId);
    if (!contract) return;

    // Check if contract still needs AMSC code and has NSN data
    if (!contract.cde_g && contract.national_stock_number) {
      // Check if we don't already have an NSN AMSC workflow queued
      const hasNsnWorkflow = workflowQueue.some(item => 
        item.contractId === completedContractId && item.type === 'nsn_amsc'
      );

      if (!hasNsnWorkflow) {
        addToWorkflowQueue(contract, 'nsn_amsc');
      }
    }
  }, [contracts, workflowQueue, addToWorkflowQueue]);

  // Process workflow queue
  const processWorkflowQueue = useCallback(async () => {
    const pendingWorkflows = workflowQueue.filter(item => item.status === 'pending');
    const availableSlots = maxConcurrentWorkflows - runningWorkflowsRef.current.size;

    if (pendingWorkflows.length === 0 || availableSlots <= 0) {
      return;
    }

    // Process available workflows
    const workflowsToProcess = pendingWorkflows.slice(0, availableSlots);
    
    for (const workflow of workflowsToProcess) {
      if (runningWorkflowsRef.current.has(workflow.contractId)) {
        continue;
      }

      // Mark as running
      setWorkflowQueue(prev => prev.map(item => 
        item.contractId === workflow.contractId ? { ...item, status: 'running' } : item
      ));
      
      runningWorkflowsRef.current.add(workflow.contractId);

      try {
        let result = null;
        
        if (workflow.type === 'rfq_pdf') {
          // Trigger RFQ PDF workflow
          result = await triggerPullSingleRfqPdf(workflow.solicitationNumber);
        } else if (workflow.type === 'nsn_amsc') {
          // Trigger NSN AMSC workflow
          result = await triggerExtractNsnAmsc(workflow.contractId, workflow.nsn);
          
          // If NSN AMSC workflow completed successfully, we might have updated closed status
          // The workflow now automatically updates the closed field based on DIBBS response
          if (result) {
            console.log(`NSN AMSC workflow completed for contract ${workflow.contractId}`);
            // Note: The closed field is automatically updated by the workflow
            // No additional action needed here
          }
        }

        // Update workflow status
        setWorkflowQueue(prev => prev.map(item => 
          item.contractId === workflow.contractId 
            ? { ...item, status: result ? 'completed' : 'failed' }
            : item
        ));

        // If RFQ PDF workflow completed successfully, check if we should queue NSN AMSC
        if (result && workflow.type === 'rfq_pdf') {
          // Wait a bit for the RFQ PDF to be processed, then check for NSN AMSC
          setTimeout(() => {
            checkForNsnAmscWorkflow(workflow.contractId);
          }, 5000); // 5 second delay
        }

        // Update stats
        setStats(prev => ({
          ...prev,
          workflowsTriggered: prev.workflowsTriggered + 1,
          workflowsCompleted: prev.workflowsCompleted + (result ? 1 : 0),
          workflowsFailed: prev.workflowsFailed + (result ? 0 : 1)
        }));

        if (result) {
          toast({
            title: 'Workflow Started',
            description: `${workflow.type === 'rfq_pdf' ? 'RFQ PDF' : 'NSN AMSC'} workflow started for ${workflow.solicitationNumber}`,
          });
        }

      } catch (error) {
        console.error(`Error processing workflow for contract ${workflow.contractId}:`, error);
        
        // Mark as failed
        setWorkflowQueue(prev => prev.map(item => 
          item.contractId === workflow.contractId ? { ...item, status: 'failed' } : item
        ));

        // Update stats
        setStats(prev => ({
          ...prev,
          workflowsTriggered: prev.workflowsTriggered + 1,
          workflowsFailed: prev.workflowsFailed + 1
        }));

        toast({
          title: 'Workflow Failed',
          description: `Failed to start ${workflow.type === 'rfq_pdf' ? 'RFQ PDF' : 'NSN AMSC'} workflow for ${workflow.solicitationNumber}`,
          variant: 'destructive',
        });
      } finally {
        runningWorkflowsRef.current.delete(workflow.contractId);
      }
    }
  }, [workflowQueue, maxConcurrentWorkflows, triggerPullSingleRfqPdf, triggerExtractNsnAmsc, toast, checkForNsnAmscWorkflow]);

  // Start watching
  const startWatching = useCallback(() => {
    if (isWatching) return;

    setIsWatching(true);
    
    // Initial check
    checkAndQueueContracts();
    
    // Set up interval
    intervalRef.current = setInterval(() => {
      checkAndQueueContracts();
      processWorkflowQueue();
    }, checkInterval);

    toast({
      title: 'Contract Watcher Started',
      description: 'Automatically monitoring contracts for missing AMSC codes',
    });
  }, [isWatching, checkInterval]); // Remove function dependencies that cause re-renders

  // Stop watching
  const stopWatching = useCallback(() => {
    if (!isWatching) return;

    setIsWatching(false);
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    toast({
      title: 'Contract Watcher Stopped',
      description: 'No longer monitoring contracts automatically',
    });
  }, [isWatching]); // Remove toast dependency that causes re-renders

  // Manually trigger workflows for a specific contract
  const triggerWorkflowsForContract = useCallback(async (contract: any) => {
    if (!contract.solicitation_number || !contract.national_stock_number) {
      toast({
        title: 'Missing Data',
        description: 'Contract is missing solicitation number or NSN',
        variant: 'destructive',
      });
      return false;
    }

    // Check if contract already has AMSC code
    if (contract.cde_g) {
      toast({
        title: 'Workflow Not Needed',
        description: 'Contract already has AMSC code extracted',
        variant: 'default',
      });
      return false;
    }

    // Check if workflows are already queued for this contract
    const hasWorkflows = workflowQueue.some(item => 
      item.contractId === contract.id && 
      (item.type === 'rfq_pdf' || item.type === 'nsn_amsc')
    );

    if (hasWorkflows) {
      toast({
        title: 'Workflow Already Queued',
        description: 'Workflows are already queued for this contract',
        variant: 'default',
      });
      return false;
    }

    // Add to workflow queue
    addToWorkflowQueue(contract, 'rfq_pdf');
    
    return true;
  }, [workflowQueue]); // Remove function dependencies that cause re-renders

  // Clean up completed/failed workflows from queue
  const cleanupWorkflowQueue = useCallback(() => {
    setWorkflowQueue(prev => prev.filter(item => 
      item.status === 'pending' || item.status === 'running'
    ));
  }, []); // No dependencies needed

  // Refresh contract data and clean up completed workflows
  const refreshContractData = useCallback(async () => {
    try {
      // Clean up workflows for contracts that now have AMSC codes
      setWorkflowQueue(prev => prev.filter(item => {
        const contract = contracts.find(c => c.id === item.contractId);
        if (!contract) return false; // Contract no longer exists
        
        // Remove workflows for contracts that now have AMSC codes
        if (contract.cde_g) return false;
        
        // Keep pending and running workflows
        if (item.status === 'pending' || item.status === 'running') return true;
        
        // Remove completed and failed workflows
        return false;
      }));
      
      toast({
        title: 'Contract Data Refreshed',
        description: 'Updated workflow queue based on current contract status',
      });
    } catch (error) {
      console.error('Error refreshing contract data:', error);
      toast({
        title: 'Refresh Failed',
        description: 'Failed to refresh contract data',
        variant: 'destructive',
      });
    }
  }, [contracts]); // Keep only contracts as dependency

  // Auto-start watching when enabled
  useEffect(() => {
    if (enabled && autoTrigger) {
      startWatching();
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [enabled, autoTrigger]); // Remove startWatching from dependencies

  // Clean up workflow queue every 5 minutes
  useEffect(() => {
    const cleanupInterval = setInterval(cleanupWorkflowQueue, 5 * 60 * 1000);
    return () => clearInterval(cleanupInterval);
  }, []); // Remove cleanupWorkflowQueue from dependencies

  // Auto-cleanup workflows when contracts get AMSC codes
  useEffect(() => {
    const contractsWithAmsc = contracts.filter(contract => contract.cde_g);
    const contractsWithoutAmsc = contracts.filter(contract => !contract.cde_g);
    
    // Update stats
    setStats(prev => ({
      ...prev,
      totalContracts: contracts.length,
      contractsWithoutAmsc: contractsWithoutAmsc.length
    }));
    
    // Clean up completed workflows for contracts that now have AMSC codes
    setWorkflowQueue(prev => prev.filter(item => {
      const contract = contracts.find(c => c.id === item.contractId);
      if (!contract) return false;
      
      // Remove workflows for contracts that now have AMSC codes
      if (contract.cde_g) return false;
      
      // Keep pending and running workflows
      if (item.status === 'pending' || item.status === 'running') return true;
      
      // Remove completed and failed workflows
      return false;
    }));
  }, [contracts]); // Keep only contracts as dependency

  return {
    // State
    isWatching,
    workflowQueue,
    stats,
    
    // Actions
    startWatching,
    stopWatching,
    triggerWorkflowsForContract,
    cleanupWorkflowQueue,
    refreshContractData,
    
    // Configuration
    config: {
      enabled,
      checkInterval,
      maxConcurrentWorkflows,
      autoTrigger
    }
  };
};
