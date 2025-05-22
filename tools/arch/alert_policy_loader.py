"""
Alert policy loader for ARCH message routing and alert triggers.
"""

from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator

class AlertActionType(str, Enum):
    """Types of alert actions."""
    CONSOLE_LOG = "console_log"
    WEBHOOK = "webhook"

class AlertCondition(BaseModel):
    """Alert condition configuration."""
    type: str  # error or task_result
    agent: Optional[str] = "*"  # Optional agent filter
    retry_count: Optional[int] = None
    error_code: Optional[str] = None
    score_below: Optional[float] = None
    score_above: Optional[float] = None
    duration_above: Optional[float] = None
    status: Optional[str] = None

class AlertAction(BaseModel):
    """Alert action configuration."""
    notify: str  # human or webhook
    method: Optional[str] = None  # For console_log
    url: Optional[str] = None  # For webhook
    headers: Optional[Dict[str, str]] = None
    template: Optional[str] = None
    level: Optional[str] = "info"  # For console_log
    message: Optional[str] = None
    timeout_seconds: Optional[int] = 10

class AlertRule(BaseModel):
    """Alert rule configuration."""
    name: str
    enabled: bool = True
    condition: AlertCondition
    action: AlertAction

class AlertPolicy(BaseModel):
    """Complete alert policy configuration."""
    version: str
    description: Optional[str] = None
    rules: List[AlertRule]

def load_alert_policy(policy_path: Union[str, Path]) -> AlertPolicy:
    """
    Load and validate an alert policy from a YAML file.
    
    Args:
        policy_path: Path to the policy YAML file
        
    Returns:
        Validated AlertPolicy instance
        
    Raises:
        FileNotFoundError: If policy file doesn't exist
        ValueError: If policy validation fails
    """
    import yaml
    
    policy_path = Path(policy_path)
    if not policy_path.exists():
        raise FileNotFoundError(f"Alert policy file not found: {policy_path}")
    
    try:
        with open(policy_path) as f:
            policy_data = yaml.safe_load(f)
        
        return AlertPolicy(**policy_data)
    except Exception as e:
        raise ValueError(f"Failed to load alert policy: {str(e)}") 