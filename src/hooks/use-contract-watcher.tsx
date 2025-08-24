import { useState, useEffect, useCallback, useRef } from 'react';
import { useContractQueue } from './use-database';
import { useWorkflow } from './use-workflow';
import { supabase } from '@/integrations/supabase/client';

interface ContractWatcherConfig {
  enabled?: boolean;
  checkInterval?: number; // milliseconds
  maxConcurrentWorkflows?: number;
  autoTrigger?: boolean;
  uploadedDocuments?: Array<{
    originalFileName: string;
    storagePath: string;
    [key: string]: any;
  }>;
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
    autoTrigger = true,
    uploadedDocuments = []
  } = config;

  const { data: contracts = [] } = useContractQueue();
  const { triggerPullSingleRfqPdf, triggerExtractNsnAmsc } = useWorkflow();
  
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

    console.log(`   📝 Adding workflow to queue: ${type} for ${contract.solicitation_number}`);
    console.log(`   📝 Queue item:`, queueItem);
    
    setWorkflowQueue(prev => {
      const newQueue = [...prev, queueItem];
      console.log(`   📝 Previous queue size: ${prev.length}, New queue size: ${newQueue.length}`);
      console.log(`   📝 New queue items:`, newQueue);
      return newQueue;
    });
    
    // Use console.log instead of toast to prevent dependency issues
    console.log(`${type === 'rfq_pdf' ? 'RFQ PDF' : 'NSN AMSC'} workflow queued for ${contract.solicitation_number}`);
  }, []); // No dependencies needed

  // Check for contracts needing workflows and queue them
  const checkAndQueueContracts = useCallback(() => {
    if (!enabled || !autoTrigger) {
      console.log('⚠️  Contract checking disabled - enabled:', enabled, 'autoTrigger:', autoTrigger);
      return;
    }

    console.log('🔍 Checking for contracts needing workflows...');
    const contractsNeedingWorkflows = findContractsNeedingWorkflows();
    
    console.log(`   - Found ${contractsNeedingWorkflows.length} contracts needing workflows`);
    console.log(`   - Current workflow queue state: ${workflowQueue.length} items`);
    console.log(`   - Current pending workflows: ${workflowQueue.filter(item => item.status === 'pending').length}`);
    
    if (contractsNeedingWorkflows.length === 0) return;

    // Process each contract based on workflow requirements
    for (const contract of contractsNeedingWorkflows) {
      // Check if we already have ANY workflow queued for this contract (pending or running)
      const hasAnyWorkflow = workflowQueue.some(item => 
        item.contractId === contract.id && 
        (item.status === 'pending' || item.status === 'running')
      );

      if (hasAnyWorkflow) {
        console.log(`   ⏸️  Contract ${contract.solicitation_number} already has workflow queued`);
        continue;
      }

      // Determine which workflows to trigger based on current state
      const needsAmsc = !contract.cde_g; // AMSC code is null
      const needsRfqPdf = !uploadedDocuments.some(doc => 
        doc.originalFileName.includes(contract.solicitation_number || '') && 
        doc.originalFileName.endsWith('.PDF')
      ); // RFQ PDF not in bucket

      console.log(`   📊 Contract ${contract.solicitation_number} analysis:`);
      console.log(`      - Needs AMSC: ${needsAmsc}`);
      console.log(`      - Needs RFQ PDF: ${needsRfqPdf}`);

      if (needsAmsc && needsRfqPdf) {
        // AMSC code null and RFQ PDF not in bucket - run both workflows
        console.log(`   ➕ Queuing RFQ PDF workflow for contract ${contract.solicitation_number}`);
        addToWorkflowQueue(contract, 'rfq_pdf');
      } else if (needsAmsc && !needsRfqPdf) {
        // AMSC code null but RFQ PDF in bucket - only run NSN extract
        console.log(`   ➕ Queuing NSN AMSC workflow for contract ${contract.solicitation_number}`);
        addToWorkflowQueue(contract, 'nsn_amsc');
      } else if (!needsAmsc && needsRfqPdf) {
        // AMSC code not null but RFQ PDF not in bucket - run nothing
        console.log(`   ⏸️  Contract ${contract.solicitation_number} has AMSC code but no RFQ PDF - no action needed`);
      } else {
        // AMSC code not null and RFQ PDF in bucket - run nothing
        console.log(`   ⏸️  Contract ${contract.solicitation_number} has both AMSC code and RFQ PDF - no action needed`);
      }
    }

    // Update stats
    setStats(prev => ({
      ...prev,
      totalContracts: contracts.length,
      contractsWithoutAmsc: contractsNeedingWorkflows.length
    }));
  }, [enabled, autoTrigger, findContractsNeedingWorkflows, workflowQueue, contracts.length, addToWorkflowQueue, uploadedDocuments]);

  // Check if we should queue NSN AMSC workflow after RFQ PDF completion
  const checkForNsnAmscWorkflow = useCallback((completedContractId: string) => {
    const contract = contracts.find(c => c.id === completedContractId);
    if (!contract) return;

    // Check if contract still needs AMSC code and has NSN data
    if (!contract.cde_g && contract.national_stock_number) {
      // Check if we don't already have ANY workflow queued for this contract
      const hasAnyWorkflow = workflowQueue.some(item => 
        item.contractId === completedContractId && 
        (item.status === 'pending' || item.status === 'running')
      );

      if (!hasAnyWorkflow) {
        addToWorkflowQueue(contract, 'nsn_amsc');
      }
    }
  }, [contracts, workflowQueue, addToWorkflowQueue]);

  // Process workflow queue
  const processWorkflowQueue = useCallback(async () => {
    console.log('⚙️  Processing workflow queue...');
    
    const pendingWorkflows = workflowQueue.filter(item => item.status === 'pending');
    const availableSlots = maxConcurrentWorkflows - runningWorkflowsRef.current.size;

    console.log(`   - Pending workflows: ${pendingWorkflows.length}`);
    console.log(`   - Available slots: ${availableSlots}`);
    console.log(`   - Currently running: ${runningWorkflowsRef.current.size}`);

    if (pendingWorkflows.length === 0 || availableSlots <= 0) {
      console.log('   ⏸️  No pending workflows or no available slots');
      return;
    }

    // Process available workflows
    const workflowsToProcess = pendingWorkflows.slice(0, availableSlots);
    console.log(`   - Processing ${workflowsToProcess.length} workflows`);
    
    for (const workflow of workflowsToProcess) {
      if (runningWorkflowsRef.current.has(workflow.contractId)) {
        console.log(`   ⏸️  Workflow for ${workflow.solicitationNumber} already running`);
        continue;
      }

      console.log(`   🚀 Starting ${workflow.type} workflow for ${workflow.solicitationNumber}`);

      // Mark as running
      setWorkflowQueue(prev => prev.map(item => 
        item.contractId === workflow.contractId ? { ...item, status: 'running' } : item
      ));
      
      runningWorkflowsRef.current.add(workflow.contractId);

      try {
        let result = null;
        
        if (workflow.type === 'rfq_pdf') {
          // Trigger RFQ PDF workflow via Supabase Edge Function
          console.log(`   📡 Triggering RFQ PDF workflow for ${workflow.solicitationNumber}`);
          result = await triggerPullSingleRfqPdf(workflow.solicitationNumber);
        } else if (workflow.type === 'nsn_amsc') {
          // Trigger NSN AMSC workflow via Supabase Edge Function
          console.log(`   📡 Triggering NSN AMSC workflow for contract ${workflow.contractId}`);
          result = await triggerExtractNsnAmsc(workflow.contractId, workflow.nsn);
          
          // If NSN AMSC workflow completed successfully, we might have updated closed status
          // The workflow now automatically updates the closed field based on DIBBS response
          if (result) {
            console.log(`✅ NSN AMSC workflow completed for contract ${workflow.contractId}`);
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
          console.log(`✅ Workflow Started: ${workflow.type === 'rfq_pdf' ? 'RFQ PDF' : 'NSN AMSC'} workflow started for ${workflow.solicitationNumber}`);
        } else {
          console.log(`❌ Workflow Failed to Start: ${workflow.type === 'rfq_pdf' ? 'RFQ PDF' : 'NSN AMSC'} workflow for ${workflow.solicitationNumber}`);
        }

      } catch (error) {
        console.error(`❌ Error processing workflow for contract ${workflow.contractId}:`, error);
        
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

        console.log(`❌ Workflow Failed: Failed to start ${workflow.type === 'rfq_pdf' ? 'RFQ PDF' : 'NSN AMSC'} workflow for ${workflow.solicitationNumber}`);
      } finally {
        runningWorkflowsRef.current.delete(workflow.contractId);
      }
    }
  }, [workflowQueue, maxConcurrentWorkflows, triggerPullSingleRfqPdf, triggerExtractNsnAmsc, checkForNsnAmscWorkflow]);

  // Start watching
  const startWatching = useCallback(() => {
    if (isWatching) return;

    setIsWatching(true);
    
    // Initial check
    checkAndQueueContracts();
    
    // Set up interval for checking contracts and processing queue
    intervalRef.current = setInterval(() => {
      console.log('🔄 Contract Watcher Interval Running...');
      console.log(`   - Current queue size: ${workflowQueue.length}`);
      console.log(`   - Pending workflows: ${workflowQueue.filter(item => item.status === 'pending').length}`);
      console.log(`   - Running workflows: ${workflowQueue.filter(item => item.status === 'running').length}`);
      
      checkAndQueueContracts();
      
      // Add a small delay to ensure state updates are processed before processing the queue
      setTimeout(() => {
        console.log('⏳ Processing workflow queue after delay...');
        console.log(`   - Queue state after delay: ${workflowQueue.length} items`);
        console.log(`   - Pending after delay: ${workflowQueue.filter(item => item.status === 'pending').length}`);
        processWorkflowQueue();
        cleanupCompletedWorkflows(); // Clean up completed workflows
      }, 100); // 100ms delay
    }, checkInterval);

    // Use console.log instead of toast to prevent dependency issues
    console.log('Contract Watcher Started - Automatically monitoring contracts for missing AMSC codes');
  }, [isWatching, checkInterval]); // Remove function dependencies that cause re-renders

  // Stop watching
  const stopWatching = useCallback(() => {
    if (!isWatching) return;

    setIsWatching(false);
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // Use console.log instead of toast to prevent dependency issues
    console.log('Contract Watcher Stopped - No longer monitoring contracts automatically');
  }, [isWatching]); // Remove toast dependency that causes re-renders

  // Manually trigger workflows for a specific contract
  const triggerWorkflowsForContract = useCallback(async (contract: any) => {
    if (!contract.solicitation_number || !contract.national_stock_number) {
      console.log('Missing Data: Contract is missing solicitation number or NSN');
      return false;
    }

    // Check if contract already has AMSC code
    if (contract.cde_g) {
      console.log('Workflow Not Needed: Contract already has AMSC code extracted');
      return false;
    }

    // Check if workflows are already queued for this contract
    const hasWorkflows = workflowQueue.some(item => 
      item.contractId === contract.id && 
      (item.type === 'rfq_pdf' || item.type === 'nsn_amsc')
    );

    if (hasWorkflows) {
      console.log('Workflow Already Queued: Workflows are already queued for this contract');
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

  // Clean up completed/failed workflows and update stats
  const cleanupCompletedWorkflows = useCallback(() => {
    setWorkflowQueue(prev => {
      const newQueue = prev.filter(item => 
        item.status === 'pending' || item.status === 'running'
      );
      
      // Count completed and failed workflows for stats
      const completedCount = prev.filter(item => item.status === 'completed').length;
      const failedCount = prev.filter(item => item.status === 'failed').length;
      
      // Update stats
      setStats(prev => ({
        ...prev,
        workflowsCompleted: prev.workflowsCompleted + completedCount,
        workflowsFailed: prev.workflowsFailed + failedCount
      }));
      
      return newQueue;
    });
  }, []);

  // Clear entire workflow queue (for debugging)
  const clearWorkflowQueue = useCallback(() => {
    setWorkflowQueue([]);
    setStats(prev => ({
      ...prev,
      workflowsTriggered: 0,
      workflowsCompleted: 0,
      workflowsFailed: 0
    }));
  }, []);

  // Refresh contract data and clean up completed workflows
  const refreshContractData = useCallback(async () => {
    try {
      // Clean up workflows for contracts that now have AMSC codes
      setWorkflowQueue(prev => {
        const newQueue = prev.filter(item => {
          const contract = contracts.find(c => c.id === item.contractId);
          if (!contract) return false; // Contract no longer exists
          
          // Remove workflows for contracts that now have AMSC codes
          if (contract.cde_g) return false;
          
          // Keep pending and running workflows
          if (item.status === 'pending' || item.status === 'running') return true;
          
          // Remove completed and failed workflows
          return false;
        });
        
        return newQueue;
      });
      
      // Use console.log instead of toast to prevent dependency issues
      console.log('Contract data refreshed - workflow queue updated');
      
    } catch (error) {
      console.error('Error refreshing contract data:', error);
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
    // Only run this effect when contracts change, not on every render
    if (contracts.length === 0) return;
    
    // Update stats without triggering workflow queue changes
    setStats(prev => ({
      ...prev,
      totalContracts: contracts.length,
      contractsWithoutAmsc: contracts.filter(contract => !contract.cde_g).length
    }));
  }, [contracts.length]); // Only depend on contracts.length, not the entire contracts array

  // Separate effect for workflow queue cleanup to prevent infinite loops
  useEffect(() => {
    // Only run this effect when contracts change, not on every render
    if (contracts.length === 0) return;
    
    // Clean up completed workflows for contracts that now have AMSC codes
    setWorkflowQueue(prev => {
      const newQueue = prev.filter(item => {
        const contract = contracts.find(c => c.id === item.contractId);
        if (!contract) return false;
        
        // Remove workflows for contracts that now have AMSC codes
        if (contract.cde_g) return false;
        
        // Keep pending and running workflows
        if (item.status === 'pending' || item.status === 'running') return true;
        
        // Remove completed and failed workflows
        return false;
      });
      
      return newQueue;
    });
  }, [contracts.map(c => c.id + ':' + c.cde_g).join(',')]); // Create a stable dependency string

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
    clearWorkflowQueue, // Add new action
    
    // Configuration
    config: {
      enabled,
      checkInterval,
      maxConcurrentWorkflows,
      autoTrigger
    }
  };
};
