"""
Phase policy loader for ARCH message routing and execution rules.
"""

from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator

class EscalationLevel(str, Enum):
    """Escalation levels for message routing."""
    NONE = "none"
    AGENT = "agent"
    HUMAN = "human"

class PhaseOverride(BaseModel):
    """Phase-specific override for routing rules."""
    phase: str
    destination: Optional[str] = None
    escalation_level: Optional[EscalationLevel] = None
    max_retries: Optional[int] = None
    retry_delay: Optional[int] = None

class Condition(BaseModel):
    """Condition for rule matching."""
    field: str
    operator: str
    value: Any

class RoutingRule(BaseModel):
    """Base routing rule configuration."""
    id: str
    destination: str
    escalation_level: EscalationLevel = EscalationLevel.NONE
    max_retries: int = 3
    retry_delay: int = 60
    phase_overrides: List[PhaseOverride] = Field(default_factory=list)
    conditions: List[Condition] = Field(default_factory=list)

class EscalationRule(BaseModel):
    """Escalation rule from phase policy."""
    type: str
    description: str
    retry_count: int = 3
    retry_delay_minutes: int = 5
    escalate_if_unresolved: bool = True
    escalation_timeout_hours: int = 2
    immediate_human_notification: bool = False

class PhasePolicy(BaseModel):
    """Complete phase policy configuration."""
    task_result_rules: List[RoutingRule] = Field(default_factory=list)
    error_rules: List[RoutingRule] = Field(default_factory=list)
    input_rules: List[RoutingRule] = Field(default_factory=list)
    escalation_rules: List[EscalationRule] = Field(default_factory=list)
    active_phase: Optional[str] = None
    autonomy_level: Optional[str] = None

def load_policy(policy_path: Union[str, Path]) -> PhasePolicy:
    """
    Load and validate a phase policy from a YAML file.
    
    Args:
        policy_path: Path to the policy YAML file
        
    Returns:
        Validated PhasePolicy instance
        
    Raises:
        FileNotFoundError: If policy file doesn't exist
        ValueError: If policy validation fails
    """
    import yaml
    
    policy_path = Path(policy_path)
    if not policy_path.exists():
        raise FileNotFoundError(f"Policy file not found: {policy_path}")
    
    try:
        with open(policy_path) as f:
            policy_data = yaml.safe_load(f)
        
        return PhasePolicy(**policy_data)
    except Exception as e:
        raise ValueError(f"Failed to load policy: {str(e)}") 