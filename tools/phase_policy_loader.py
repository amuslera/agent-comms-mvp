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


class PhaseOverride(BaseModel):
    autonomy_level: Optional[AutonomyLevel] = None
    permissions: Optional[Permissions] = None
    escalation_rules: Optional[List[EscalationRule]] = None


class PhasePolicy(BaseModel):
    # Core phase configuration
    active_phase: str = "Phase 1"
    phase_description: str = ""
    cto_scope: CTOScope = CTOScope.TASK_LEVEL
    
    # Autonomy settings
    autonomy_level: AutonomyLevel = AutonomyLevel.MEDIUM
    max_concurrent_tasks: int = 5
    max_execution_time_hours: int = 8
    budget_limit_usd: Optional[float] = None
    
    # Permissions and rules
    permissions: Permissions = Field(default_factory=Permissions)
    escalation_rules: List[EscalationRule] = Field(default_factory=list)
    notify_methods: List[NotificationMethod] = Field(default_factory=list)
    quality_gates: List[QualityGate] = Field(default_factory=list)
    
    # Resource and learning
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)
    learning_policy: LearningPolicy = Field(default_factory=LearningPolicy)
    rollback_policy: RollbackPolicy = Field(default_factory=RollbackPolicy)
    
    # Governance
    compliance: Compliance = Field(default_factory=Compliance)
    emergency_procedures: EmergencyProcedures = Field(default_factory=EmergencyProcedures)
    
    # Phase-specific overrides
    phase_overrides: Dict[str, PhaseOverride] = Field(default_factory=dict)
    
    # Metadata
    policy_version: str = "1.0.0"
    created_date: Optional[str] = None
    last_updated: Optional[str] = None
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    expires_date: Optional[str] = None

    @field_validator('max_concurrent_tasks')
    @classmethod
    def validate_concurrent_tasks(cls, v):
        if v <= 0:
            raise ValueError('max_concurrent_tasks must be positive')
        return v

    @field_validator('max_execution_time_hours')
    @classmethod
    def validate_execution_time(cls, v):
        if v <= 0:
            raise ValueError('max_execution_time_hours must be positive')
        return v

    @field_validator('budget_limit_usd')
    @classmethod
    def validate_budget(cls, v):
        if v is not None and v < 0:
            raise ValueError('budget_limit_usd must be non-negative')
        return v

    @model_validator(mode='after')
    def validate_phase_consistency(self):
        """Ensure phase overrides are consistent with active phase"""
        if self.active_phase and self.active_phase in self.phase_overrides:
            # Apply phase-specific overrides
            override = self.phase_overrides[self.active_phase]
            if override.autonomy_level:
                self.autonomy_level = override.autonomy_level
            if override.permissions:
                self.permissions = override.permissions
            if override.escalation_rules:
                self.escalation_rules.extend(override.escalation_rules)
        
        return self


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
            self._policy = PhasePolicy(**policy_data)
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
            active_phase="Phase 1",
            phase_description="Safe default configuration",
            cto_scope=CTOScope.TASK_LEVEL,
            autonomy_level=AutonomyLevel.LOW,
            max_concurrent_tasks=1,
            max_execution_time_hours=1,
            permissions=Permissions(
                create_branches=True,
                merge_to_main=False,
                create_releases=False,
                modify_core_architecture=False,
                add_dependencies=False,
                create_new_agents=False,
                modify_security_policies=False,
                external_integrations=False,
                infrastructure_changes=False
            ),
            escalation_rules=[
                EscalationRule(
                    type="default",
                    description="Default escalation for all errors",
                    retry_count=1,
                    retry_delay_minutes=5,
                    escalate_if_unresolved=True,
                    escalation_timeout_hours=1
                )
            ]
        )

    def get_policy(self) -> PhasePolicy:
        """Get current policy, loading if necessary"""
        if not self._policy:
            return self.load_policy()
        return self._policy

    def is_action_permitted(self, action: str) -> bool:
        """Check if a specific action is permitted under current policy"""
        policy = self.get_policy()
        permissions = policy.permissions
        
        action_map = {
            'create_branch': permissions.create_branches,
            'merge_to_main': permissions.merge_to_main,
            'create_release': permissions.create_releases,
            'modify_architecture': permissions.modify_core_architecture,
            'add_dependency': permissions.add_dependencies,
            'create_agent': permissions.create_new_agents,
            'modify_security': permissions.modify_security_policies,
            'external_integration': permissions.external_integrations,
            'infrastructure_change': permissions.infrastructure_changes,
        }
        
        return action_map.get(action, False)

    def get_escalation_rule(self, error_type: str) -> Optional[EscalationRule]:
        """Get escalation rule for specific error type"""
        policy = self.get_policy()
        
        for rule in policy.escalation_rules:
            if rule.type == error_type:
                return rule
        
        # Return default rule if no specific rule found
        for rule in policy.escalation_rules:
            if rule.type == "error" or rule.type == "default":
                return rule
        
        return None

    def should_escalate(self, error_type: str, retry_count: int) -> bool:
        """Determine if error should be escalated based on policy"""
        rule = self.get_escalation_rule(error_type)
        
        if not rule:
            return True  # Escalate by default if no rule found
        
        if rule.immediate_human_notification:
            return True
        
        if retry_count >= rule.retry_count:
            return rule.escalate_if_unresolved
        
        return False

    def get_resource_limit(self, resource_type: str) -> int:
        """Get resource limit for specific resource type"""
        policy = self.get_policy()
        limits = policy.resource_limits
        
        limit_map = {
            'api_calls': limits.max_api_calls_per_hour,
            'file_operations': limits.max_file_operations_per_hour,
            'network_requests': limits.max_network_requests_per_hour,
            'subprocess_executions': limits.max_subprocess_executions_per_hour,
        }
        
        return limit_map.get(resource_type, 100)  # Default limit

    def save_policy(self, policy: PhasePolicy) -> None:
        """Save policy to YAML file"""
        policy_dict = policy.model_dump()
        
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