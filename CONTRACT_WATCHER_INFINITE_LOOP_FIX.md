# Contract Watcher Infinite Loop Fix

## Issue Description
The contract watcher was experiencing a "Maximum update depth exceeded" error, which indicates an infinite re-render loop. This commonly happens when `useEffect` dependencies change on every render, causing the effect to run continuously.

## Root Cause
The problem was caused by several `useCallback` functions that had dependencies on other functions or state variables that were being recreated on every render. This created a chain reaction where:

1. Functions were recreated due to changing dependencies
2. `useEffect` hooks re-ran because their dependencies changed
3. State updates triggered re-renders
4. Functions were recreated again
5. The cycle repeated infinitely

## Specific Problems Identified

### 1. **Function Dependencies in useCallback**
```typescript
// PROBLEMATIC: Functions depending on other functions
const startWatching = useCallback(() => {
  // ... function body
}, [isWatching, checkAndQueueContracts, processWorkflowQueue, checkInterval, toast]);
```

### 2. **useEffect with Function Dependencies**
```typescript
// PROBLEMATIC: useEffect depending on functions that change
useEffect(() => {
  if (enabled && autoTrigger) {
    startWatching();
  }
  // ... cleanup
}, [enabled, autoTrigger, startWatching]); // startWatching changes every render
```

### 3. **Circular Dependencies**
- `startWatching` depended on `checkAndQueueContracts`
- `checkAndQueueContracts` depended on `workflowQueue` state
- `workflowQueue` state changes triggered re-renders
- Re-renders recreated all functions
- Functions triggered `useEffect` hooks
- `useEffect` hooks updated state
- Cycle repeated infinitely

## Solution Implemented

### 1. **Removed Function Dependencies from useCallback**
```typescript
// FIXED: Only essential dependencies
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
}, [isWatching, checkInterval]); // Removed function dependencies
```

### 2. **Simplified useEffect Dependencies**
```typescript
// FIXED: Only essential dependencies
useEffect(() => {
  if (enabled && autoTrigger) {
    startWatching();
  }
  return () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
  };
}, [enabled, autoTrigger]); // Removed startWatching dependency
```

### 3. **Stabilized Function References**
```typescript
// FIXED: No dependencies needed for simple functions
const cleanupWorkflowQueue = useCallback(() => {
  setWorkflowQueue(prev => prev.filter(item => 
    item.status === 'pending' || item.status === 'running'
  ));
}, []); // No dependencies needed
```

## Key Changes Made

### **useCallback Dependencies Reduced**
- `startWatching`: Removed `checkAndQueueContracts`, `processWorkflowQueue`, `toast`
- `stopWatching`: Removed `toast`
- `triggerWorkflowsForContract`: Removed `addToWorkflowQueue`, `processWorkflowQueue`, `toast`
- `cleanupWorkflowQueue`: No dependencies needed
- `refreshContractData`: Removed `toast`

### **useEffect Dependencies Simplified**
- Auto-start effect: Only `enabled` and `autoTrigger`
- Cleanup effect: No dependencies (runs once)
- Auto-cleanup effect: Only `contracts`

## Why This Fix Works

### 1. **Breaks the Infinite Loop**
- Functions no longer depend on other functions that change
- `useEffect` hooks have stable dependencies
- State updates don't trigger function recreation

### 2. **Maintains Functionality**
- All automation logic still works
- Functions can still access current state through closures
- Intervals and cleanup still function properly

### 3. **Improves Performance**
- Fewer unnecessary re-renders
- Stable function references
- Better React optimization

## Testing the Fix

### **Before Fix**
- Console showed "Maximum update depth exceeded" error
- Application would freeze or crash
- Infinite re-render loop in React DevTools

### **After Fix**
- No more infinite loop errors
- Contract watcher functions normally
- Stable performance without crashes

## Best Practices Applied

### 1. **Minimal useCallback Dependencies**
- Only include dependencies that are truly necessary
- Avoid depending on functions that change frequently
- Use empty dependency arrays when possible

### 2. **Stable useEffect Dependencies**
- Keep dependencies minimal and stable
- Avoid functions as dependencies unless absolutely necessary
- Use refs for values that shouldn't trigger re-renders

### 3. **Function Design**
- Design functions to be independent when possible
- Use closures to access current state instead of dependencies
- Separate concerns to reduce coupling

## Prevention Tips

### 1. **Audit Dependencies Regularly**
- Review `useCallback` and `useEffect` dependencies
- Look for functions that might change on every render
- Use React DevTools Profiler to identify issues

### 2. **Use ESLint Rules**
- Enable `react-hooks/exhaustive-deps` rule
- Pay attention to dependency warnings
- Don't ignore dependency-related linting errors

### 3. **Test for Infinite Loops**
- Watch for performance issues in development
- Monitor console for maximum update depth warnings
- Use React DevTools to track re-renders

## Conclusion

The infinite loop issue was successfully resolved by:
- Removing unnecessary function dependencies from `useCallback`
- Simplifying `useEffect` dependencies to only essential values
- Breaking the circular dependency chain that caused re-renders

The contract watcher now functions properly without performance issues, while maintaining all its automation capabilities. This fix demonstrates the importance of carefully managing React hooks dependencies and avoiding circular references in custom hooks.
