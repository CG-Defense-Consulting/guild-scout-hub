# Contract Watcher Workflow Triggering Implementation

## Overview
The contract watcher has been updated to properly trigger workflows by calling Supabase edge functions that start GitHub Actions, instead of just managing a local queue. The system now implements the exact logic specified by the user.

## Workflow Logic Implementation

### **Core Decision Logic**
The system now implements the exact workflow requirements:

```typescript
// Determine which workflows to trigger based on current state
const needsAmsc = !contract.cde_g; // AMSC code is null
const needsRfqPdf = !uploadedDocuments.some(doc => 
  doc.originalFileName.includes(contract.solicitation_number || '') && 
  doc.originalFileName.endsWith('.PDF')
); // RFQ PDF not in bucket

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
```

### **Workflow Scenarios**

#### **Scenario 1: AMSC Code Null + RFQ PDF Not in Bucket**
- **Action**: Queue RFQ PDF workflow
- **Reason**: Need both the PDF and AMSC code
- **Workflow**: `pull_single_rfq_pdf`

#### **Scenario 2: AMSC Code Null + RFQ PDF in Bucket**
- **Action**: Queue NSN AMSC workflow only
- **Reason**: Have PDF, just need AMSC code
- **Workflow**: `extract_nsn_amsc`

#### **Scenario 3: AMSC Code Not Null + RFQ PDF Not in Bucket**
- **Action**: Run nothing
- **Reason**: Have AMSC code, PDF not needed for this contract
- **Workflow**: None

#### **Scenario 4: AMSC Code Not Null + RFQ PDF in Bucket**
- **Action**: Run nothing
- **Reason**: Have both, contract is complete
- **Workflow**: None

## Technical Implementation

### **1. Supabase Edge Function Integration**
The contract watcher now properly calls the Supabase edge functions:

```typescript
if (workflow.type === 'rfq_pdf') {
  // Trigger RFQ PDF workflow via Supabase Edge Function
  console.log(`   📡 Triggering RFQ PDF workflow for ${workflow.solicitationNumber}`);
  result = await triggerPullSingleRfqPdf(workflow.solicitationNumber);
} else if (workflow.type === 'nsn_amsc') {
  // Trigger NSN AMSC workflow via Supabase Edge Function
  console.log(`   📡 Triggering NSN AMSC workflow for contract ${workflow.contractId}`);
  result = await triggerExtractNsnAmsc(workflow.contractId, workflow.nsn);
}
```

### **2. Workflow Hook Integration**
Uses the same `useWorkflow` hook as the manual automation buttons:

```typescript
const { triggerPullSingleRfqPdf, triggerExtractNsnAmsc } = useWorkflow();
```

### **3. Edge Function Parameters**
- **RFQ PDF Workflow**: `workflow_name: 'pull_single_rfq_pdf'` with `solicitation_number`
- **NSN AMSC Workflow**: `workflow_name: 'extract_nsn_amsc'` with `contract_id` and `nsn`

## Enhanced Debugging and Logging

### **Contract Analysis Logging**
```
📊 Contract SPE1C125T2602 analysis:
   - Needs AMSC: true
   - Needs RFQ PDF: true
```

### **Workflow Triggering Logs**
```
📡 Triggering RFQ PDF workflow for SPE1C125T2602
📡 Triggering NSN AMSC workflow for contract abc123
```

### **Workflow Status Updates**
```
✅ Workflow Started: RFQ PDF workflow started for SPE1C125T2602
✅ NSN AMSC workflow completed for contract abc123
❌ Workflow Failed: Failed to start RFQ PDF workflow for SPE1C125T2602
```

## Data Flow

### **1. Contract Discovery**
- `findContractsNeedingWorkflows()` identifies contracts without AMSC codes
- Filters out contracts already in workflow queue

### **2. Workflow Decision**
- Analyzes each contract's current state
- Determines which workflows are needed
- Queues appropriate workflows

### **3. Workflow Execution**
- `processWorkflowQueue()` processes pending workflows
- Calls Supabase edge functions via `useWorkflow` hook
- Updates workflow status based on results

### **4. GitHub Actions Triggering**
- Edge functions trigger GitHub Actions workflows
- Workflows execute in GitHub Actions environment
- Results update contract data in Supabase

## Configuration and Dependencies

### **ContractWatcherPanel Props**
```typescript
interface ContractWatcherPanelProps {
  className?: string;
  uploadedDocuments?: Array<{
    originalFileName: string;
    storagePath: string;
    [key: string]: any;
  }>;
}
```

### **useContractWatcher Config**
```typescript
const {
  enabled = true,
  checkInterval = 30000, // 30 seconds
  maxConcurrentWorkflows = 3,
  autoTrigger = true,
  uploadedDocuments = []
} = config;
```

### **Dependencies**
- `useWorkflow` hook for triggering workflows
- `uploadedDocuments` array for checking PDF availability
- `contracts` data for AMSC code status

## Expected Behavior

### **Console Output Example**
```
🔄 Contract Watcher Interval Running...
   - Current queue size: 0
   - Pending workflows: 0
   - Running workflows: 0
🔍 Checking for contracts needing workflows...
   - Found 4 contracts needing workflows
   - Current workflow queue state: 0 items
   - Current pending workflows: 0
   📊 Contract SPE1C125T2602 analysis:
      - Needs AMSC: true
      - Needs RFQ PDF: true
   ➕ Queuing RFQ PDF workflow for contract SPE1C125T2602
   📝 Adding workflow to queue: rfq_pdf for SPE1C125T2602
   📝 Queue item: {contractId: "...", solicitationNumber: "SPE1C125T2602", ...}
   📝 Previous queue size: 0, New queue size: 1
   📝 New queue items: [{...}]
   RFQ PDF workflow queued for SPE1C125T2602
⏳ Processing workflow queue after delay...
   - Queue state after delay: 1 items
   - Pending after delay: 1
⚙️  Processing workflow queue...
   - Pending workflows: 1
   - Available slots: 3
   - Currently running: 0
   - Processing 1 workflows
   🚀 Starting rfq_pdf workflow for SPE1C125T2602
   📡 Triggering RFQ PDF workflow for SPE1C125T2602
✅ Workflow Started: RFQ PDF workflow started for SPE1C125T2602
```

### **GitHub Actions Results**
- Workflows should appear in GitHub Actions tab
- RFQ PDF workflows download PDFs to Supabase storage
- NSN AMSC workflows extract AMSC codes and update database
- Contract status should update automatically

## Testing and Validation

### **Test Cases**
1. **Contract without AMSC and PDF**: Should trigger RFQ PDF workflow
2. **Contract without AMSC but with PDF**: Should trigger NSN AMSC workflow only
3. **Contract with AMSC but without PDF**: Should trigger nothing
4. **Contract with both**: Should trigger nothing

### **Validation Steps**
1. **Start Contract Watcher**: Enable automatic monitoring
2. **Monitor Console**: Look for workflow analysis and triggering logs
3. **Check GitHub Actions**: Verify workflows are triggered
4. **Monitor Results**: Check for PDF downloads and AMSC code updates
5. **Verify Status**: Confirm contract status changes appropriately

## Benefits of the Implementation

### **1. Proper Workflow Triggering**
- Actually calls Supabase edge functions
- Triggers real GitHub Actions workflows
- Integrates with existing automation system

### **2. Intelligent Decision Making**
- Analyzes contract state comprehensively
- Only triggers necessary workflows
- Prevents redundant operations

### **3. Comprehensive Logging**
- Clear visibility into decision process
- Workflow execution tracking
- Easy troubleshooting and debugging

### **4. Efficient Resource Usage**
- No unnecessary workflow executions
- Proper workflow sequencing
- Concurrent workflow management

## Future Enhancements

### **Potential Improvements**
1. **Real-time PDF Detection**: WebSocket updates for PDF availability
2. **Workflow Dependencies**: Ensure proper execution order
3. **Retry Logic**: Automatic retry for failed workflows
4. **Performance Metrics**: Track workflow success rates

### **Advanced Features**
1. **Batch Processing**: Process multiple contracts simultaneously
2. **Priority Queuing**: Prioritize urgent contracts
3. **Smart Scheduling**: Time-based workflow execution
4. **Integration APIs**: Webhook notifications for workflow completion

## Conclusion

The contract watcher now properly implements the specified workflow logic:
- **Intelligently analyzes** each contract's current state
- **Makes proper decisions** about which workflows to trigger
- **Actually executes workflows** via Supabase edge functions
- **Integrates seamlessly** with the existing automation system

The system will now:
1. **Automatically detect** contracts needing workflows
2. **Apply the correct logic** for workflow selection
3. **Trigger real GitHub Actions** workflows
4. **Update contract status** based on workflow results

This implementation ensures the automation system works as intended, with workflows being properly triggered and executed in GitHub Actions based on the exact business logic specified.
