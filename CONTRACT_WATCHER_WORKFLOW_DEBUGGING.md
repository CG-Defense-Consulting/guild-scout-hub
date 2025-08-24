# Contract Watcher Workflow Debugging Guide

## Issue Description
The contract watcher was not actually triggering workflows in GitHub Actions, despite showing pending workflows in the queue. This debugging guide helps identify and resolve the issue.

## Root Cause Analysis

### **Potential Issues**
1. **Workflow Queue Processing**: The `processWorkflowQueue` function might not be running
2. **Interval Execution**: The interval that calls workflow processing might not be working
3. **Dependency Problems**: Function dependencies might be preventing execution
4. **Workflow Triggering**: The actual GitHub Actions triggers might be failing

## Debugging Improvements Added

### 1. **Enhanced Interval Logging**
```typescript
// Set up interval for checking contracts and processing queue
intervalRef.current = setInterval(() => {
  console.log('🔄 Contract Watcher Interval Running...');
  console.log(`   - Current queue size: ${workflowQueue.length}`);
  console.log(`   - Pending workflows: ${workflowQueue.filter(item => item.status === 'pending').length}`);
  console.log(`   - Running workflows: ${workflowQueue.filter(item => item.status === 'running').length}`);
  
  checkAndQueueContracts();
  processWorkflowQueue();
  cleanupCompletedWorkflows();
}, checkInterval);
```

**What This Shows:**
- Whether the interval is running at all
- Current queue state on each interval
- Queue size and workflow status counts

### 2. **Contract Checking Debugging**
```typescript
const checkAndQueueContracts = useCallback(() => {
  if (!enabled || !autoTrigger) {
    console.log('⚠️  Contract checking disabled - enabled:', enabled, 'autoTrigger:', autoTrigger);
    return;
  }

  console.log('🔍 Checking for contracts needing workflows...');
  const contractsNeedingWorkflows = findContractsNeedingWorkflows();
  
  console.log(`   - Found ${contractsNeedingWorkflows.length} contracts needing workflows`);
  
  // ... rest of function
}, [enabled, autoTrigger, findContractsNeedingWorkflows, workflowQueue, contracts.length, addToWorkflowQueue]);
```

**What This Shows:**
- Whether contract checking is enabled
- How many contracts need workflows
- Which contracts are being queued
- Which contracts are skipped

### 3. **Workflow Processing Debugging**
```typescript
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
    console.log(`   🚀 Starting ${workflow.type} workflow for ${workflow.solicitationNumber}`);
    // ... rest of processing
  }
}, [workflowQueue, maxConcurrentWorkflows]);
```

**What This Shows:**
- Whether workflow processing is running
- Queue processing status
- Available processing slots
- Individual workflow execution

## How to Debug the Issue

### **Step 1: Check Console Logs**
Open the browser console and look for these log messages:

1. **🔄 Contract Watcher Interval Running...** - Should appear every 30 seconds
2. **🔍 Checking for contracts needing workflows...** - Should appear on each interval
3. **⚙️  Processing workflow queue...** - Should appear on each interval

### **Step 2: Verify Interval Execution**
If you don't see the interval logs:
- Check if the watcher is started (`isWatching` should be true)
- Verify the interval is set up correctly
- Check for JavaScript errors in the console

### **Step 3: Check Contract Discovery**
Look for these logs:
- **Found X contracts needing workflows** - Should show contracts without AMSC codes
- **Queuing RFQ PDF workflow for contract X** - Should show when workflows are added
- **Contract X already has workflow queued** - Should show when duplicates are prevented

### **Step 4: Verify Workflow Processing**
Look for these logs:
- **Pending workflows: X** - Should show pending items in queue
- **Available slots: X** - Should show available processing capacity
- **Starting X workflow for Y** - Should show when workflows actually start

## Common Issues and Solutions

### **Issue 1: No Interval Logs**
**Symptoms:** No "🔄 Contract Watcher Interval Running..." messages
**Possible Causes:**
- Watcher not started
- JavaScript errors preventing interval setup
- Component unmounted

**Solutions:**
- Check if `startWatching()` was called
- Look for JavaScript errors in console
- Verify component is still mounted

### **Issue 2: No Contract Discovery**
**Symptoms:** No "Found X contracts needing workflows" messages
**Possible Causes:**
- No contracts without AMSC codes
- `enabled` or `autoTrigger` set to false
- Contract data not loaded

**Solutions:**
- Check if contracts have `cde_g` values
- Verify watcher configuration
- Ensure contract data is loaded

### **Issue 3: No Workflow Processing**
**Symptoms:** No "⚙️  Processing workflow queue..." messages
**Possible Causes:**
- No pending workflows in queue
- All workflow slots occupied
- Function not being called

**Solutions:**
- Check queue status in ContractWatcherPanel
- Verify `maxConcurrentWorkflows` setting
- Check for function dependency issues

### **Issue 4: Workflows Not Triggering GitHub Actions**
**Symptoms:** See "Starting X workflow" but no GitHub Actions triggered
**Possible Causes:**
- `triggerPullSingleRfqPdf` or `triggerExtractNsnAmsc` failing
- GitHub Actions configuration issues
- Authentication problems

**Solutions:**
- Check browser network tab for failed requests
- Verify GitHub Actions workflow files
- Check authentication tokens

## Debugging Checklist

### **Before Starting Debugging**
- [ ] Open browser console
- [ ] Start contract watcher
- [ ] Check for JavaScript errors
- [ ] Verify contract data is loaded

### **During Debugging**
- [ ] Monitor interval logs (every 30 seconds)
- [ ] Check contract discovery logs
- [ ] Verify workflow processing logs
- [ ] Look for error messages

### **After Debugging**
- [ ] Identify the specific issue
- [ ] Apply appropriate fix
- [ ] Test the solution
- [ ] Monitor for recurrence

## Expected Console Output

### **Normal Operation**
```
🔄 Contract Watcher Interval Running...
   - Current queue size: 2
   - Pending workflows: 1
   - Running workflows: 1
🔍 Checking for contracts needing workflows...
   - Found 3 contracts needing workflows
   ➕ Queuing RFQ PDF workflow for contract SPE4A625T29KC
   ⏸️  Contract SPE4A625T30KC already has workflow queued
⚙️  Processing workflow queue...
   - Pending workflows: 1
   - Available slots: 2
   - Currently running: 1
   - Processing 1 workflows
   🚀 Starting rfq_pdf workflow for SPE4A625T29KC
✅ Workflow Started: RFQ PDF workflow started for SPE4A625T29KC
```

### **No Workflows Needed**
```
🔄 Contract Watcher Interval Running...
   - Current queue size: 0
   - Pending workflows: 0
   - Running workflows: 0
🔍 Checking for contracts needing workflows...
   - Found 0 contracts needing workflows
⚙️  Processing workflow queue...
   - Pending workflows: 0
   - Available slots: 3
   - Currently running: 0
   ⏸️  No pending workflows or no available slots
```

## Troubleshooting Steps

### **If No Logs Appear**
1. Check if contract watcher is enabled
2. Verify component is mounted
3. Look for JavaScript errors
4. Check browser console settings

### **If Logs Appear But No Workflows**
1. Check contract data for AMSC codes
2. Verify workflow queue status
3. Check GitHub Actions configuration
4. Test manual workflow triggering

### **If Workflows Start But Fail**
1. Check network requests in browser
2. Verify GitHub Actions workflow files
3. Check authentication and permissions
4. Review workflow error logs

## Conclusion

The enhanced debugging provides comprehensive visibility into:
- **Interval Execution**: Whether the watcher is running
- **Contract Discovery**: How many contracts need workflows
- **Queue Management**: Current workflow queue status
- **Workflow Processing**: Individual workflow execution details

Use these logs to identify exactly where the workflow triggering process is failing and apply the appropriate fix. The detailed logging should make it clear whether the issue is with:
- Contract discovery
- Queue management
- Workflow processing
- GitHub Actions triggering
- Or something else entirely
