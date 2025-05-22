"""
Phase Policy Loader
Loads and validates execution policies for ARCH/CTO agent autonomy
"""

import yaml
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
from dataclasses import dataclass, field


class AutonomyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FULL = "full"


class CTOScope(str, Enum):
    COMPLETE_PHASE = "complete_phase"
    TASK_LEVEL = "task_level"
    APPROVAL_REQUIRED = "approval_required"


class NotificationType(str, Enum):
    PROGRESS_UPDATE = "progress_update"
    TASK_COMPLETION = "task_completion"
    ERROR_NOTIFICATION = "error_notification"
    CRITICAL_ALERT = "critical_alert"
    PHASE_COMPLETION = "phase_completion"


class NotificationTarget(str, Enum):
    SUMMARY_TO_INBOX = "summary_to_inbox"
    HUMAN_NOTIFICATION = "human_notification"


class Urgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Permissions(BaseModel):
    create_branches: bool = True
    merge_to_main: bool = False
    create_releases: bool = False
    modify_core_architecture: bool = False
    add_dependencies: bool = True
    create_new_agents: bool = False
    modify_security_policies: bool = False
    external_integrations: bool = False
    infrastructure_changes: bool = False


class EscalationRule(BaseModel):
    type: str
    description: str = ""
    retry_count: int = 0
    retry_delay_minutes: int = 5
    escalate_if_unresolved: bool = True
    escalation_timeout_hours: int = 2
    escalate: Optional[bool] = None
    immediate_human_notification: bool = False
    documentation_required: bool = False

    @field_validator('retry_count')
    @classmethod
    def validate_retry_count(cls, v):
        if v < 0:
            raise ValueError('retry_count must be non-negative')
        return v

    @field_validator('retry_delay_minutes')
    @classmethod
    def validate_retry_delay(cls, v):
        if v < 0:
            raise ValueError('retry_delay_minutes must be non-negative')
        return v


class NotificationMethod(BaseModel):
    type: NotificationType
    target: NotificationTarget
    frequency: str = "immediate"
    urgency: Optional[Urgency] = None


class QualityGate(BaseModel):
    type: str
    required: bool = True
    auto_approve_threshold: Optional[float] = None
    min_coverage: Optional[float] = None
    run_integration_tests: bool = False
    auto_generate: bool = False
    human_review_required: bool = True
    auto_fix_low_risk: bool = False
    escalate_medium_high: bool = True

    @field_validator('auto_approve_threshold')
    @classmethod
    def validate_threshold(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('auto_approve_threshold must be between 0 and 1')
        return v

    @field_validator('min_coverage')
    @classmethod
    def validate_coverage(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('min_coverage must be between 0 and 1')
        return v


class ResourceLimits(BaseModel):
    max_api_calls_per_hour: int = 1000
    max_file_operations_per_hour: int = 500
    max_network_requests_per_hour: int = 200
    max_subprocess_executions_per_hour: int = 100

    @field_validator('max_api_calls_per_hour', 'max_file_operations_per_hour', 'max_network_requests_per_hour', 'max_subprocess_executions_per_hour')
    @classmethod
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError('Resource limits must be positive integers')
        return v


class LearningPolicy(BaseModel):
    enabled: bool = True
    collect_performance_metrics: bool = True
    adapt_retry_strategies: bool = True
    optimize_task_routing: bool = True
    share_insights_with_agents: bool = True


class RollbackPolicy(BaseModel):
    auto_rollback_on_critical_error: bool = True
    create_backup_before_major_changes: bool = True
    max_rollback_attempts: int = 3
    rollback_timeout_minutes: int = 10

    @field_validator('max_rollback_attempts')
    @classmethod
    def validate_rollback_attempts(cls, v):
        if v < 0:
            raise ValueError('max_rollback_attempts must be non-negative')
        return v


class Compliance(BaseModel):
    audit_trail: bool = True
    decision_logging: bool = True
    approval_history: bool = True
    change_tracking: bool = True


class EmergencyProcedures(BaseModel):
    emergency_stop_enabled: bool = True
    emergency_contacts: List[str] = Field(default_factory=list)
    emergency_rollback: bool = True
    safe_mode_on_repeated_failures: bool = True
    safe_mode_threshold: int = 5

    @field_validator('safe_mode_threshold')
    @classmethod
    def validate_threshold(cls, v):
        if v <= 0:
            raise ValueError('safe_mode_threshold must be positive')
        return v


class PhaseOverride:
    def __init__(self, phase: str, max_retries: Optional[int] = None, retry_delay: Optional[int] = None):
        self.phase = phase
        self.max_retries = max_retries
        self.retry_delay = retry_delay


class Condition:
    def __init__(self, field: str, operator: str, value: Any = None, values: List[Any] = field(default_factory=list)):
        self.field = field
        self.operator = operator
        self.value = value
        self.values = values


class PolicyRule:
    def __init__(self, id: str, destination: str, escalation_level: str, max_retries: int = 3, retry_delay: int = 60, phase_overrides: List[PhaseOverride] = field(default_factory=list), conditions: List[Condition] = field(default_factory=list)):
        self.id = id
        self.destination = destination
        self.escalation_level = escalation_level
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.phase_overrides = phase_overrides
        self.conditions = conditions


class PhasePolicy:
    def __init__(self, task_result_rules: List[PolicyRule] = field(default_factory=list), error_rules: List[PolicyRule] = field(default_factory=list), input_rules: List[PolicyRule] = field(default_factory=list)):
        self.task_result_rules = task_result_rules
        self.error_rules = error_rules
        self.input_rules = input_rules


class PolicyLoader:
    """Loads and validates phase execution policies"""
    
    def __init__(self, policy_file: Optional[Union[str, Path]] = None):
        """
        Initialize policy loader
        
        Args:
            policy_file: Path to policy YAML file. If None, uses default locations
        """
        self.policy_file = self._resolve_policy_file(policy_file)
        self._policy: Optional[PhasePolicy] = None
        self._load_timestamp: Optional[datetime] = None

    def _resolve_policy_file(self, policy_file: Optional[Union[str, Path]]) -> Path:
        """Resolve policy file path with fallback to default locations"""
        if policy_file:
            return Path(policy_file)
        
        # Try default locations
        default_locations = [
            Path.cwd() / "phase_policy.yaml",
            Path.cwd() / "config" / "phase_policy.yaml",
            Path(__file__).parent.parent / "phase_policy.yaml",
        ]
        
        for location in default_locations:
            if location.exists():
                return location
        
        # If no file found, use the first default location
        return default_locations[0]

    def load_policy(self, reload: bool = False) -> PhasePolicy:
        """
        Load and validate policy from YAML file
        
        Args:
            reload: Force reload even if policy is already loaded
            
        Returns:
            Validated PhasePolicy instance
            
        Raises:
            FileNotFoundError: If policy file doesn't exist
            ValueError: If policy validation fails
            yaml.YAMLError: If YAML parsing fails
        """
        if self._policy and not reload:
            return self._policy

        if not self.policy_file.exists():
            # Create default policy if file doesn't exist
            self._policy = self._create_safe_default_policy()
            return self._policy

        try:
            with open(self.policy_file, 'r', encoding='utf-8') as f:
                policy_data = yaml.safe_load(f)
            
            if not policy_data:
                policy_data = {}
            
            # Validate and create policy instance
            self._policy = self._create_policy_from_data(policy_data)
            self._load_timestamp = datetime.now()
            
            return self._policy
            
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse policy YAML: {e}")
        except Exception as e:
            # Fallback to safe default on any error
            print(f"Warning: Failed to load policy ({e}), using safe defaults")
            self._policy = self._create_safe_default_policy()
            return self._policy

    def _create_safe_default_policy(self) -> PhasePolicy:
        """Create a safe default policy for fallback scenarios"""
        return PhasePolicy(
            task_result_rules=[],
            error_rules=[],
            input_rules=[]
        )

    def _create_policy_from_data(self, data: dict) -> PhasePolicy:
        """Create a PhasePolicy instance from loaded YAML data"""
        task_result_rules = [self._parse_rule(rule) for rule in data.get("task_result_rules", [])]
        error_rules = [self._parse_rule(rule) for rule in data.get("error_rules", [])]
        input_rules = [self._parse_rule(rule) for rule in data.get("input_rules", [])]
        return PhasePolicy(
            task_result_rules=task_result_rules,
            error_rules=error_rules,
            input_rules=input_rules
        )

    def _parse_rule(self, rule_dict: dict) -> PolicyRule:
        """Parse a single rule from the YAML data"""
        # Validate escalation_level
        valid_levels = {"none", "agent", "human"}
        if rule_dict.get("escalation_level") not in valid_levels:
            raise ValueError(f"Invalid escalation level: {rule_dict.get('escalation_level')}")
        # Parse phase_overrides
        phase_overrides = [self._parse_phase_override(po) for po in rule_dict.get("phase_overrides", [])]
        # Parse conditions
        conditions = [self._parse_condition(c) for c in rule_dict.get("conditions", [])]
        return PolicyRule(
            id=rule_dict["id"],
            destination=rule_dict["destination"],
            escalation_level=rule_dict["escalation_level"],
            max_retries=rule_dict.get("max_retries", 3),
            retry_delay=rule_dict.get("retry_delay", 60),
            phase_overrides=phase_overrides,
            conditions=conditions
        )

    def _parse_phase_override(self, po_dict: dict) -> PhaseOverride:
        """Parse a PhaseOverride from the YAML data"""
        return PhaseOverride(
            phase=po_dict["phase"],
            max_retries=po_dict.get("max_retries"),
            retry_delay=po_dict.get("retry_delay")
        )

    def _parse_condition(self, c_dict: dict) -> Condition:
        """Parse a Condition from the YAML data"""
        return Condition(
            field=c_dict["field"],
            operator=c_dict["operator"],
            value=c_dict.get("value"),
            values=c_dict.get("values", [])
        )

    def get_policy(self) -> PhasePolicy:
        """Get current policy, loading if necessary"""
        if not self._policy:
            return self.load_policy()
        return self._policy

    def is_action_permitted(self, action: str) -> bool:
        """Check if a specific action is permitted under current policy"""
        policy = self.get_policy()
        for rule in policy.task_result_rules + policy.error_rules + policy.input_rules:
            if rule.destination == action:
                return True
        return False

    def get_escalation_rule(self, error_type: str) -> Optional[PolicyRule]:
        """Get escalation rule for specific error type"""
        policy = self.get_policy()
        
        for rule in policy.error_rules:
            if rule.id == error_type:
                return rule
        
        # Return default rule if no specific rule found
        for rule in policy.error_rules:
            if rule.id == "error" or rule.id == "default":
                return rule
        
        return None

    def should_escalate(self, error_type: str, retry_count: int) -> bool:
        """Determine if error should be escalated based on policy"""
        rule = self.get_escalation_rule(error_type)
        
        if not rule:
            return True  # Escalate by default if no rule found
        
        if rule.immediate_human_notification:
            return True
        
        if retry_count >= rule.max_retries:
            return rule.escalate_if_unresolved
        
        return False

    def get_resource_limit(self, resource_type: str) -> int:
        """Get resource limit for specific resource type"""
        policy = self.get_policy()
        for rule in policy.task_result_rules + policy.error_rules + policy.input_rules:
            if rule.destination == resource_type:
                return rule.max_retries * rule.retry_delay
        
        return 100  # Default limit

    def save_policy(self, policy: PhasePolicy) -> None:
        """Save policy to YAML file"""
        policy_dict = {
            "task_result_rules": [rule.__dict__ for rule in policy.task_result_rules],
            "error_rules": [rule.__dict__ for rule in policy.error_rules],
            "input_rules": [rule.__dict__ for rule in policy.input_rules]
        }
        
        # Ensure parent directory exists
        self.policy_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.policy_file, 'w', encoding='utf-8') as f:
            yaml.dump(policy_dict, f, default_flow_style=False, sort_keys=False)
        
        self._policy = policy
        self._load_timestamp = datetime.now()


# Global policy loader instance
_policy_loader: Optional[PolicyLoader] = None


def get_policy_loader(policy_file: Optional[Union[str, Path]] = None) -> PolicyLoader:
    """Get global policy loader instance"""
    global _policy_loader
    if _policy_loader is None:
        _policy_loader = PolicyLoader(policy_file)
    return _policy_loader


def get_current_policy() -> PhasePolicy:
    """Get current phase policy"""
    return get_policy_loader().get_policy()


def is_action_permitted(action: str) -> bool:
    """Check if action is permitted under current policy"""
    return get_policy_loader().is_action_permitted(action)


def should_escalate_error(error_type: str, retry_count: int) -> bool:
    """Check if error should be escalated"""
    return get_policy_loader().should_escalate(error_type, retry_count)


def load_policy(policy_path: Path) -> PhasePolicy:
    """Load and return a PhasePolicy from the given YAML file path."""
    loader = PolicyLoader(policy_path)
    return loader.load_policy()


if __name__ == "__main__":
    # Example usage and testing
    loader = PolicyLoader()
    
    try:
        policy = loader.load_policy()
        print(f"Loaded policy for {policy.active_phase}")
        print(f"Autonomy level: {policy.autonomy_level}")
        print(f"Can merge to main: {policy.permissions.merge_to_main}")
        print(f"Max concurrent tasks: {policy.max_concurrent_tasks}")
        
        # Test permission checking
        print(f"Can create branch: {loader.is_action_permitted('create_branch')}")
        print(f"Can modify architecture: {loader.is_action_permitted('modify_architecture')}")
        
        # Test escalation rules
        print(f"Should escalate error after 2 retries: {loader.should_escalate('error', 2)}")
        print(f"Should escalate critical error immediately: {loader.should_escalate('critical_error', 0)}")
        
    except Exception as e:
        print(f"Error loading policy: {e}")
        print("Using safe default policy")