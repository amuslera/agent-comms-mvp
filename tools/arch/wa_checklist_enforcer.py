"""
WA Checklist Enforcer Module

This module automatically enforces WA_CHECKLIST.md requirements on all WA tasks
during the planning phase. It adds checklist requirements to task descriptions
and creates validation hooks for compliance review.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from pathlib import Path


class WAChecklistEnforcer:
    """Enforces WA checklist requirements on all WA agent tasks."""
    
    def __init__(self, checklist_path: str = "WA_CHECKLIST.md"):
        """
        Initialize the WA Checklist Enforcer.
        
        Args:
            checklist_path: Path to the WA_CHECKLIST.md file
        """
        self.checklist_path = checklist_path
        self.checklist_summary = self._load_checklist_summary()
        self.validation_hooks_dir = Path("postbox/WA/validation_hooks")
        self.validation_hooks_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_checklist_summary(self) -> str:
        """Load a summary of key checklist requirements."""
        # Default summary if checklist file not found
        default_summary = """
📋 **WA Checklist Requirements:**
- ✅ Test all UI changes across different viewport sizes
- ✅ Verify accessibility (ARIA labels, keyboard navigation)
- ✅ Run component tests if modifying existing components
- ✅ Check browser console for errors/warnings
- ✅ Validate form inputs and error states
- ✅ Ensure consistent styling with design system
- ✅ Test loading and error states
- ✅ Verify responsive behavior
"""
        
        if os.path.exists(self.checklist_path):
            try:
                with open(self.checklist_path, 'r') as f:
                    content = f.read()
                    # Extract key points (this is a simplified extraction)
                    # In a real implementation, you'd parse the markdown more carefully
                    return default_summary
            except Exception as e:
                print(f"Warning: Could not load checklist from {self.checklist_path}: {e}")
        
        return default_summary
    
    def enhance_wa_task_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance a WA task message with checklist enforcement.
        
        Args:
            message: The original MCP message for a WA task
            
        Returns:
            Enhanced message with checklist requirements
        """
        # Only process messages for WA agent
        if message.get("recipient_id") != "WA":
            return message
        
        # Create a copy to avoid modifying original
        enhanced_message = json.loads(json.dumps(message))
        
        # Add checklist summary to task description
        if "payload" in enhanced_message and "content" in enhanced_message["payload"]:
            content = enhanced_message["payload"]["content"]
            
            # Enhance description with checklist reminder
            original_description = content.get("description", "")
            enhanced_description = f"{original_description}\n\n{self.checklist_summary}"
            content["description"] = enhanced_description
            
            # Add metadata about checklist enforcement
            if "metadata" not in enhanced_message:
                enhanced_message["metadata"] = {}
            
            enhanced_message["metadata"]["wa_checklist_enforced"] = True
            enhanced_message["metadata"]["checklist_version"] = "1.0"
            enhanced_message["metadata"]["enforcement_timestamp"] = datetime.now().isoformat()
        
        return enhanced_message
    
    def create_validation_hook(self, task_id: str, validation_data: Dict[str, Any]) -> str:
        """
        Create a validation hook file for later compliance review.
        
        Args:
            task_id: The task ID
            validation_data: Data needed for validation
            
        Returns:
            Path to the created validation hook file
        """
        hook_filename = f"{task_id}_validation_hook.json"
        hook_path = self.validation_hooks_dir / hook_filename
        
        hook_data = {
            "task_id": task_id,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "validation_data": validation_data,
            "checklist_items": [
                {"item": "UI tested across viewports", "status": "pending"},
                {"item": "Accessibility verified", "status": "pending"},
                {"item": "Component tests run", "status": "pending"},
                {"item": "Console errors checked", "status": "pending"},
                {"item": "Form validation tested", "status": "pending"},
                {"item": "Styling consistency checked", "status": "pending"},
                {"item": "Loading states tested", "status": "pending"},
                {"item": "Responsive behavior verified", "status": "pending"}
            ]
        }
        
        with open(hook_path, 'w') as f:
            json.dump(hook_data, f, indent=2)
        
        return str(hook_path)
    
    def get_pending_validations(self) -> List[Dict[str, Any]]:
        """Get all pending validation hooks."""
        pending = []
        
        for hook_file in self.validation_hooks_dir.glob("*_validation_hook.json"):
            try:
                with open(hook_file, 'r') as f:
                    hook_data = json.load(f)
                    if hook_data.get("status") == "pending":
                        pending.append(hook_data)
            except Exception as e:
                print(f"Error reading hook file {hook_file}: {e}")
        
        return pending
    
    def validate_task_completion(self, task_id: str, validation_results: Dict[str, bool]) -> bool:
        """
        Validate that a WA task met all checklist requirements.
        
        Args:
            task_id: The task ID to validate
            validation_results: Dict mapping checklist items to pass/fail
            
        Returns:
            True if all requirements met, False otherwise
        """
        hook_filename = f"{task_id}_validation_hook.json"
        hook_path = self.validation_hooks_dir / hook_filename
        
        if not hook_path.exists():
            print(f"No validation hook found for task {task_id}")
            return False
        
        with open(hook_path, 'r') as f:
            hook_data = json.load(f)
        
        # Update checklist items with validation results
        all_passed = True
        for item in hook_data["checklist_items"]:
            item_name = item["item"]
            if item_name in validation_results:
                item["status"] = "passed" if validation_results[item_name] else "failed"
                if not validation_results[item_name]:
                    all_passed = False
            else:
                item["status"] = "skipped"
        
        # Update overall status
        hook_data["status"] = "validated" if all_passed else "failed"
        hook_data["validated_at"] = datetime.now().isoformat()
        
        # Save updated hook
        with open(hook_path, 'w') as f:
            json.dump(hook_data, f, indent=2)
        
        return all_passed


# Helper functions for integration with plan_runner.py

def enforce_wa_checklist_on_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper function to enforce WA checklist on a message.
    
    Args:
        message: The MCP message to enhance
        
    Returns:
        Enhanced message with checklist requirements
    """
    enforcer = WAChecklistEnforcer()
    return enforcer.enhance_wa_task_message(message)


def create_wa_validation_hook(task_id: str, validation_data: Dict[str, Any]) -> str:
    """
    Helper function to create a validation hook.
    
    Args:
        task_id: The task ID
        validation_data: Data for validation
        
    Returns:
        Path to created hook file
    """
    enforcer = WAChecklistEnforcer()
    return enforcer.create_validation_hook(task_id, validation_data)