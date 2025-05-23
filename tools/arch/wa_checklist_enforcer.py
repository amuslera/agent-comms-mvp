#!/usr/bin/env python3
"""
WA Checklist Enforcement Module

Automatically enforces WA checklist compliance during task planning and execution.
Adds checklist reminders and validation hooks to all WA task assignments.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class WAChecklistEnforcer:
    """Enforces WA checklist compliance for all WA agent tasks."""
    
    def __init__(self, checklist_path: str = "WA_CHECKLIST.md"):
        """Initialize with path to WA checklist."""
        self.checklist_path = Path(checklist_path)
        self.checklist_summary = self._generate_checklist_summary()
        self.validation_logs = []
    
    def _generate_checklist_summary(self) -> str:
        """Generate a concise summary of key WA checklist requirements."""
        summary = """
=== WA CHECKLIST REQUIREMENTS ===

📋 MANDATORY COMPLIANCE ITEMS:

1. **Branch Management**
   - Create branch: feat/TASK-XXX-description or fix/TASK-XXX-description
   - Ensure based on latest main

2. **Code Organization**
   - Components in /apps/web/src/components/
   - Pages in /apps/web/src/app/
   - Use TypeScript for all files
   - Follow naming conventions (PascalCase for components)

3. **Development Standards**
   - Use Tailwind CSS for styling
   - Ensure responsive design (mobile-first)
   - Add loading states for async operations
   - Include error boundaries where appropriate

4. **Testing Requirements**
   - Test all routes render correctly
   - Verify responsive behavior
   - Check accessibility features
   - Run npm run lint and npm run build

5. **Documentation**
   - Take screenshots of working UI
   - Update /TASK_CARDS.md with status
   - Update /postbox/WA/outbox.json with completion details

6. **RESTRICTIONS - DO NOT MODIFY**
   - CLI tools or scripts
   - Plan execution logic
   - Backend infrastructure
   - API endpoints or schemas

⚠️ REMINDER: Did WA follow the checklist? Please verify all items above!
"""
        return summary
    
    def enhance_wa_task_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance a WA task message with checklist enforcement.
        
        Args:
            message: The original MCP message for WA task
            
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
            
            # Add checklist metadata
            if "metadata" not in content:
                content["metadata"] = {}
            
            content["metadata"]["wa_checklist_enforced"] = True
            content["metadata"]["checklist_version"] = "1.0"
            content["metadata"]["enforcement_timestamp"] = datetime.now().isoformat()
            
            # Add checklist validation requirements
            if "requirements" not in content:
                content["requirements"] = []
            
            content["requirements"].extend([
                "Follow WA_CHECKLIST.md requirements",
                "Take screenshots of UI changes",
                "Update TASK_CARDS.md on completion",
                "Run lint and build checks before committing"
            ])
            
            # Add validation hook reference
            content["metadata"]["validation_hook"] = "wa_checklist_compliance_review"
        
        # Log enforcement action
        self._log_enforcement(enhanced_message)
        
        return enhanced_message
    
    def add_checklist_validation_hook(self, task_id: str, validation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a validation hook for manual checklist compliance review.
        
        Args:
            task_id: The task ID to validate
            validation_data: Data about the task for validation
            
        Returns:
            Validation hook configuration
        """
        hook = {
            "hook_id": f"wa_checklist_validation_{task_id}",
            "task_id": task_id,
            "type": "manual_review",
            "checklist_items": [
                {
                    "category": "Branch Management",
                    "items": [
                        "Branch created with correct format",
                        "Based on latest main"
                    ]
                },
                {
                    "category": "Code Standards",
                    "items": [
                        "TypeScript used for all files",
                        "Components in correct folders",
                        "Tailwind CSS for styling",
                        "Responsive design implemented"
                    ]
                },
                {
                    "category": "Testing",
                    "items": [
                        "All routes tested",
                        "Lint checks passed",
                        "Build successful"
                    ]
                },
                {
                    "category": "Documentation",
                    "items": [
                        "Screenshots captured",
                        "TASK_CARDS.md updated",
                        "Outbox notification sent"
                    ]
                }
            ],
            "validation_status": "pending",
            "created_at": datetime.now().isoformat(),
            "validation_data": validation_data
        }
        
        # Store validation hook for later review
        validation_path = Path("logs/wa_validations")
        validation_path.mkdir(parents=True, exist_ok=True)
        
        hook_file = validation_path / f"{hook['hook_id']}.json"
        with open(hook_file, 'w') as f:
            json.dump(hook, f, indent=2)
        
        return hook
    
    def validate_wa_task_completion(self, task_id: str, completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that a completed WA task followed the checklist.
        
        Args:
            task_id: The completed task ID
            completion_data: Data about the completed task
            
        Returns:
            Validation results
        """
        validation_results = {
            "task_id": task_id,
            "validation_timestamp": datetime.now().isoformat(),
            "checklist_compliance": {},
            "issues_found": [],
            "recommendations": []
        }
        
        # Check branch naming
        branch_name = completion_data.get("branch", "")
        if branch_name:
            if not (branch_name.startswith("feat/TASK-") or branch_name.startswith("fix/TASK-")):
                validation_results["issues_found"].append("Branch naming convention not followed")
                validation_results["recommendations"].append("Use feat/TASK-XXX or fix/TASK-XXX format")
        
        # Check for TypeScript files
        files_modified = completion_data.get("files_modified", [])
        js_files = [f for f in files_modified if f.endswith(".js") and "/apps/web/" in f]
        if js_files:
            validation_results["issues_found"].append(f"JavaScript files found: {js_files}")
            validation_results["recommendations"].append("Convert all JavaScript files to TypeScript")
        
        # Check for screenshots
        if not completion_data.get("screenshots_included", False):
            validation_results["issues_found"].append("No screenshots provided")
            validation_results["recommendations"].append("Include screenshots of UI changes")
        
        # Check TASK_CARDS.md update
        if "/TASK_CARDS.md" not in files_modified:
            validation_results["issues_found"].append("TASK_CARDS.md not updated")
            validation_results["recommendations"].append("Update TASK_CARDS.md with task completion details")
        
        # Check outbox update
        if "/postbox/WA/outbox.json" not in files_modified:
            validation_results["issues_found"].append("WA outbox not updated")
            validation_results["recommendations"].append("Update /postbox/WA/outbox.json with task status")
        
        # Calculate compliance score
        total_checks = 5
        passed_checks = total_checks - len(validation_results["issues_found"])
        validation_results["compliance_score"] = f"{passed_checks}/{total_checks}"
        validation_results["compliant"] = len(validation_results["issues_found"]) == 0
        
        return validation_results
    
    def _log_enforcement(self, message: Dict[str, Any]) -> None:
        """Log checklist enforcement action."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": message.get("task_id", "unknown"),
            "recipient": message.get("recipient_id", "unknown"),
            "enforcement_type": "checklist_added",
            "message_trace_id": message.get("trace_id", "unknown")
        }
        self.validation_logs.append(log_entry)
        
        # Also write to enforcement log file
        log_path = Path("logs/wa_checklist_enforcement.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_path, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def get_enforcement_summary(self) -> Dict[str, Any]:
        """Get summary of all enforcement actions."""
        return {
            "total_enforcements": len(self.validation_logs),
            "enforcement_logs": self.validation_logs,
            "checklist_version": "1.0",
            "summary_generated_at": datetime.now().isoformat()
        }


# Integration helper functions

def enforce_wa_checklist_on_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper function to enforce WA checklist on a task assignment message.
    
    Args:
        message: The original MCP message
        
    Returns:
        Enhanced message with checklist enforcement
    """
    enforcer = WAChecklistEnforcer()
    return enforcer.enhance_wa_task_message(message)


def create_wa_validation_hook(task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper function to create a validation hook for a WA task.
    
    Args:
        task_id: The task ID
        task_data: Task data for validation
        
    Returns:
        Validation hook configuration
    """
    enforcer = WAChecklistEnforcer()
    return enforcer.add_checklist_validation_hook(task_id, task_data)


def validate_wa_task(task_id: str, completion_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper function to validate a completed WA task.
    
    Args:
        task_id: The completed task ID
        completion_data: Data about task completion
        
    Returns:
        Validation results
    """
    enforcer = WAChecklistEnforcer()
    return enforcer.validate_wa_task_completion(task_id, completion_data)


if __name__ == "__main__":
    # Example usage
    sample_message = {
        "type": "task_result",
        "protocol_version": "1.3",
        "sender_id": "ARCH",
        "recipient_id": "WA",
        "trace_id": "test-trace-123",
        "task_id": "TASK-TEST-001",
        "payload": {
            "type": "task_assignment",
            "content": {
                "task_id": "TASK-TEST-001",
                "description": "Create a new dashboard component",
                "action": "create_component",
                "parameters": {
                    "component_name": "MetricsDashboard",
                    "location": "/apps/web/src/components/dashboard/"
                }
            }
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # Enforce checklist
    enhanced_message = enforce_wa_checklist_on_message(sample_message)
    print("Enhanced message:")
    print(json.dumps(enhanced_message, indent=2))
    
    # Create validation hook
    hook = create_wa_validation_hook("TASK-TEST-001", {"branch": "feat/TASK-TEST-001-metrics"})
    print("\nValidation hook created:")
    print(json.dumps(hook, indent=2))