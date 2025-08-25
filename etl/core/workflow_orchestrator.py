"""
Workflow Orchestrator

This module provides a framework for orchestrating workflows by chaining operations
together and managing shared context and batching.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from .operations import BaseOperation, OperationResult, OperationStatus

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Status of a workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class WorkflowStep:
    """Represents a step in a workflow."""
    operation: BaseOperation
    inputs: Dict[str, Any]
    depends_on: List[str] = None
    batch_config: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []
        if self.batch_config is None:
            self.batch_config = {}

class WorkflowOrchestrator:
    """
    Orchestrates the execution of workflows by chaining operations together.
    
    This class:
    1. Manages operation dependencies and execution order
    2. Handles shared context between operations
    3. Supports batching operations over multiple items
    4. Provides comprehensive logging and error handling
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize the workflow orchestrator.
        
        Args:
            name: Name of the workflow
            description: Description of what the workflow does
        """
        self.name = name
        self.description = description
        self.steps: List[WorkflowStep] = []
        self.context: Dict[str, Any] = {}
        self.status = WorkflowStatus.PENDING
        self.results: List[OperationResult] = []
        self.current_step_index = 0
        
    def add_step(self, operation: BaseOperation, inputs: Dict[str, Any] = None, 
                 depends_on: List[str] = None, batch_config: Optional[Dict[str, Any]] = None) -> 'WorkflowOrchestrator':
        """
        Add a step to the workflow.
        
        Args:
            operation: The operation to execute
            inputs: Inputs for the operation
            depends_on: List of step names this step depends on
            batch_config: Configuration for batch processing
            
        Returns:
            Self for method chaining
        """
        if inputs is None:
            inputs = {}
        
        step = WorkflowStep(
            operation=operation,
            inputs=inputs,
            depends_on=depends_on or [],
            batch_config=batch_config or {}
        )
        
        self.steps.append(step)
        logger.info(f"Added step '{operation.name}' to workflow '{self.name}'")
        
        return self
    
    def execute(self, initial_context: Optional[Dict[str, Any]] = None) -> List[OperationResult]:
        """
        Execute the workflow.
        
        Args:
            initial_context: Initial context data to share between operations
            
        Returns:
            List of operation results
        """
        try:
            logger.info(f"Starting workflow execution: {self.name}")
            self.status = WorkflowStatus.RUNNING
            self.context = initial_context or {}
            self.results = []
            self.current_step_index = 0
            
            # Validate workflow
            if not self._validate_workflow():
                raise ValueError("Workflow validation failed")
            
            # Execute steps in order
            for i, step in enumerate(self.steps):
                self.current_step_index = i
                logger.info(f"Executing step {i + 1}/{len(self.steps)}: {step.operation.name}")
                
                # Check dependencies
                if not self._check_dependencies(step):
                    raise RuntimeError(f"Step {step.operation.name} dependencies not met")
                
                # Execute the step
                if step.batch_config and step.operation.can_apply_to_batch():
                    result = self._execute_batch_step(step)
                else:
                    result = step.operation.execute(step.inputs, self.context)
                
                self.results.append(result)
                
                # Update context with step results
                self._update_context_with_result(step, result)
                
                # Check if step failed
                if not result.success:
                    logger.error(f"Step {step.operation.name} failed: {result.error}")
                    self.status = WorkflowStatus.FAILED
                    return self.results
                
                logger.info(f"Step {step.operation.name} completed successfully")
            
            # All steps completed successfully
            self.status = WorkflowStatus.COMPLETED
            logger.info(f"Workflow '{self.name}' completed successfully")
            
            return self.results
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.status = WorkflowStatus.FAILED
            raise
    
    def _validate_workflow(self) -> bool:
        """
        Validate the workflow configuration.
        
        Returns:
            True if valid, False otherwise
        """
        if not self.steps:
            logger.error("Workflow has no steps")
            return False
        
        # Check for circular dependencies
        if self._has_circular_dependencies():
            logger.error("Workflow has circular dependencies")
            return False
        
        # Check that all dependencies reference valid step names
        step_names = [step.operation.name for step in self.steps]
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in step_names:
                    logger.error(f"Step {step.operation.name} depends on unknown step: {dep}")
                    return False
        
        logger.info("Workflow validation passed")
        return True
    
    def _has_circular_dependencies(self) -> bool:
        """
        Check for circular dependencies in the workflow.
        
        Returns:
            True if circular dependencies exist, False otherwise
        """
        # Simple cycle detection using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(step_name: str) -> bool:
            if step_name in rec_stack:
                return True
            if step_name in visited:
                return False
            
            visited.add(step_name)
            rec_stack.add(step_name)
            
            # Find the step
            step = next((s for s in self.steps if s.operation.name == step_name), None)
            if step:
                for dep in step.depends_on:
                    if has_cycle(dep):
                        return True
            
            rec_stack.remove(step_name)
            return False
        
        # Check each step
        for step in self.steps:
            if has_cycle(step.operation.name):
                return True
        
        return False
    
    def _check_dependencies(self, step: WorkflowStep) -> bool:
        """
        Check if all dependencies for a step are met.
        
        Args:
            step: The step to check dependencies for
            
        Returns:
            True if all dependencies are met, False otherwise
        """
        if not step.depends_on:
            return True
        
        # Check that all dependent steps have completed successfully
        for dep_name in step.depends_on:
            dep_step = next((s for s in self.steps if s.operation.name == dep_name), None)
            if not dep_step:
                logger.error(f"Dependency {dep_name} not found for step {step.operation.name}")
                return False
            
            # Find the result for this dependency
            dep_result = None
            for i, s in enumerate(self.steps):
                if s.operation.name == dep_name:
                    if i < len(self.results):
                        dep_result = self.results[i]
                    break
            
            if not dep_result or not dep_result.success:
                logger.error(f"Dependency {dep_name} has not completed successfully for step {step.operation.name}")
                return False
        
        return True
    
    def _execute_batch_step(self, step: WorkflowStep) -> OperationResult:
        """
        Execute a step with batch processing.
        
        Args:
            step: The step to execute
            
        Returns:
            OperationResult from the batch execution
        """
        batch_config = step.batch_config
        items = batch_config.get('items', [])
        
        if not items:
            logger.warning(f"No items provided for batch step {step.operation.name}")
            return OperationResult(
                success=True,
                status=OperationStatus.COMPLETED,
                data={'processed_count': 0},
                metadata={'message': 'No items to process'}
            )
        
        logger.info(f"Executing batch step {step.operation.name} with {len(items)} items")
        
        # Execute the operation on the batch
        batch_results = step.operation.apply_to_batch(items, step.inputs, self.context)
        
        # Aggregate results
        successful = len([r for r in batch_results if r.success])
        failed = len([r for r in batch_results if not r.success])
        
        # Create aggregated result
        aggregated_result = OperationResult(
            success=failed == 0,
            status=OperationStatus.COMPLETED if failed == 0 else OperationStatus.FAILED,
            data={
                'total_items': len(items),
                'successful_items': successful,
                'failed_items': failed,
                'batch_results': batch_results
            },
            metadata={
                'step_name': step.operation.name,
                'batch_size': len(items)
            }
        )
        
        return aggregated_result
    
    def _update_context_with_result(self, step: WorkflowStep, result: OperationResult) -> None:
        """
        Update the shared context with the result of a step.
        
        Args:
            step: The step that was executed
            result: The result of the step execution
        """
        if result.success and result.data:
            # Store step result in context
            context_key = f"{step.operation.name}_result"
            self.context[context_key] = result
            
            # Also store the data directly for easy access
            self.context[step.operation.name] = result.data
            
            logger.debug(f"Updated context with result from {step.operation.name}")
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get the current workflow context.
        
        Returns:
            Dictionary containing the shared context
        """
        return self.context.copy()
    
    def get_status(self) -> WorkflowStatus:
        """
        Get the current workflow status.
        
        Returns:
            Current workflow status
        """
        return self.status
    
    def get_results(self) -> List[OperationResult]:
        """
        Get the results from all executed steps.
        
        Returns:
            List of operation results
        """
        return self.results.copy()
    
    def cleanup(self) -> None:
        """Clean up resources used by the workflow."""
        try:
            # Clean up operations that support cleanup
            for step in self.steps:
                if hasattr(step.operation, 'cleanup'):
                    try:
                        step.operation.cleanup(self.context)
                    except Exception as e:
                        logger.warning(f"Error during cleanup of {step.operation.name}: {str(e)}")
            
            # Clear context
            self.context.clear()
            logger.info("Workflow cleanup completed")
            
        except Exception as e:
            logger.warning(f"Error during workflow cleanup: {str(e)}")
    
    def __str__(self) -> str:
        return f"WorkflowOrchestrator({self.name})"
    
    def __repr__(self) -> str:
        return f"WorkflowOrchestrator(name='{self.name}', description='{self.description}', steps={len(self.steps)})"
