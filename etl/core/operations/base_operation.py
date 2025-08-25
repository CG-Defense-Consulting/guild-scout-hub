"""
Base Operation Class

Defines the interface and common functionality for all operations
that can be chained together in workflows.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class OperationStatus(Enum):
    """Status of an operation execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class OperationResult:
    """Result of an operation execution."""
    success: bool
    status: OperationStatus
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BaseOperation(ABC):
    """
    Base class for all operations that can be chained in workflows.
    
    Operations are the building blocks of workflows and can be:
    - Executed individually
    - Chained together in sequences
    - Applied to batches of data
    - Conditionally executed based on previous results
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize the base operation.
        
        Args:
            name: Unique name for this operation
            description: Human-readable description of what this operation does
        """
        self.name = name
        self.description = description
        self.status = OperationStatus.PENDING
        self.result: Optional[OperationResult] = None
        self.dependencies: List[str] = []
        self.required_inputs: List[str] = []
        self.optional_inputs: List[str] = []
        
    def add_dependency(self, operation_name: str) -> 'BaseOperation':
        """
        Add a dependency on another operation.
        
        Args:
            operation_name: Name of the operation this depends on
            
        Returns:
            Self for method chaining
        """
        if operation_name not in self.dependencies:
            self.dependencies.append(operation_name)
        return self
    
    def set_required_inputs(self, inputs: List[str]) -> 'BaseOperation':
        """
        Set the required inputs for this operation.
        
        Args:
            inputs: List of required input keys
            
        Returns:
            Self for method chaining
        """
        self.required_inputs = inputs
        return self
    
    def set_optional_inputs(self, inputs: List[str]) -> 'BaseOperation':
        """
        Set the optional inputs for this operation.
        
        Args:
            inputs: List of optional input keys
            
        Returns:
            Self for method chaining
        """
        self.optional_inputs = inputs
        return self
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """
        Validate that all required inputs are present.
        
        Args:
            inputs: Dictionary of available inputs
            
        Returns:
            True if all required inputs are present, False otherwise
        """
        missing_inputs = []
        for required_input in self.required_inputs:
            if required_input not in inputs:
                missing_inputs.append(required_input)
        
        if missing_inputs:
            logger.error(f"Operation {self.name} missing required inputs: {missing_inputs}")
            return False
        
        return True
    
    def execute(self, inputs: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> OperationResult:
        """
        Execute the operation with the given inputs.
        
        Args:
            inputs: Dictionary of inputs for this operation
            context: Optional context data shared across operations
            
        Returns:
            OperationResult containing the execution result
        """
        try:
            # Validate inputs
            if not self.validate_inputs(inputs):
                self.status = OperationStatus.FAILED
                self.result = OperationResult(
                    success=False,
                    status=OperationStatus.FAILED,
                    error=f"Missing required inputs: {[i for i in self.required_inputs if i not in inputs]}"
                )
                return self.result
            
            # Set context if provided
            if context is None:
                context = {}
            
            # Update status
            self.status = OperationStatus.RUNNING
            logger.info(f"Executing operation: {self.name}")
            
            # Execute the operation
            result = self._execute(inputs, context)
            
            # Update status and result
            self.status = result.status
            self.result = result
            
            if result.success:
                logger.info(f"Operation {self.name} completed successfully")
            else:
                logger.error(f"Operation {self.name} failed: {result.error}")
            
            return result
            
        except Exception as e:
            error_msg = f"Unexpected error in operation {self.name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            self.status = OperationStatus.FAILED
            self.result = OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error=error_msg
            )
            return self.result
    
    @abstractmethod
    def _execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> OperationResult:
        """
        Abstract method that subclasses must implement.
        
        Args:
            inputs: Dictionary of inputs for this operation
            context: Context data shared across operations
            
        Returns:
            OperationResult containing the execution result
        """
        pass
    
    def can_apply_to_batch(self) -> bool:
        """
        Check if this operation can be applied to a batch of items.
        
        Returns:
            True if the operation supports batch processing, False otherwise
        """
        return hasattr(self, 'apply_to_batch')
    
    def apply_to_batch(self, items: List[Any], inputs: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[OperationResult]:
        """
        Apply this operation to a batch of items.
        
        Args:
            items: List of items to process
            inputs: Dictionary of inputs for this operation
            context: Optional context data shared across operations
            
        Returns:
            List of OperationResult for each item
        """
        if not self.can_apply_to_batch():
            raise NotImplementedError(f"Operation {self.name} does not support batch processing")
        
        results = []
        for item in items:
            # Create item-specific inputs
            item_inputs = inputs.copy()
            item_inputs['item'] = item
            
            # Execute operation for this item
            result = self.execute(item_inputs, context)
            results.append(result)
        
        return results
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', description='{self.description}')"
