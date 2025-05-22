"""
Tests for the ARCH phase policy loader.
"""

import pytest
from pathlib import Path
from tools.arch.phase_policy_loader import load_policy, PhasePolicy, EscalationLevel

def test_load_valid_policy(mock_phase_policy):
    """Test loading a valid policy."""
    policy = load_policy(mock_phase_policy)
    
    assert policy is not None
    assert len(policy.task_result_rules) == 1
    assert len(policy.error_rules) == 1
    assert len(policy.input_rules) == 1
    
    # Verify task result rule
    task_rule = policy.task_result_rules[0]
    assert task_rule.id == "test_task_result"
    assert task_rule.destination == "ARCH"
    assert task_rule.escalation_level == EscalationLevel.NONE
    assert task_rule.max_retries == 3
    assert task_rule.retry_delay == 60
    
    # Verify error rule
    error_rule = policy.error_rules[0]
    assert error_rule.id == "test_error"
    assert error_rule.destination == "CC"
    assert error_rule.escalation_level == EscalationLevel.AGENT
    assert error_rule.max_retries == 2
    assert error_rule.retry_delay == 30
    
    # Verify input rule
    input_rule = policy.input_rules[0]
    assert input_rule.id == "test_input"
    assert input_rule.destination == "ARCH"
    assert input_rule.escalation_level == EscalationLevel.HUMAN
    assert input_rule.max_retries == 1
    assert input_rule.retry_delay == 0

def test_load_invalid_policy(tmp_path):
    """Test loading an invalid policy."""
    policy_file = tmp_path / "invalid_policy.yaml"
    policy_file.write_text("""
    task_result_rules:
      - id: test_rule
        destination: ARCH
        escalation_level: invalid_level
        max_retries: 3
        retry_delay: 60
    """)
    
    with pytest.raises(ValueError) as exc_info:
        load_policy(policy_file)
    err = str(exc_info.value)
    assert "Failed to load policy" in err
    assert "validation error" in err

def test_load_missing_policy(tmp_path):
    """Test loading a non-existent policy file."""
    policy_file = tmp_path / "nonexistent.yaml"
    
    with pytest.raises(FileNotFoundError) as exc_info:
        load_policy(policy_file)
    assert "Policy file not found" in str(exc_info.value)

def test_load_policy_with_missing_fields(tmp_path):
    """Test loading a policy with missing optional fields."""
    policy_file = tmp_path / "minimal_policy.yaml"
    policy_file.write_text("""
    task_result_rules:
      - id: test_rule
        destination: ARCH
    """)
    
    policy = load_policy(policy_file)
    assert policy is not None
    
    rule = policy.task_result_rules[0]
    assert rule.id == "test_rule"
    assert rule.destination == "ARCH"
    assert rule.escalation_level == EscalationLevel.NONE  # Default
    assert rule.max_retries == 3  # Default
    assert rule.retry_delay == 60  # Default

def test_load_policy_with_phase_overrides(tmp_path):
    """Test loading a policy with phase-specific overrides."""
    policy_file = tmp_path / "phase_policy.yaml"
    policy_file.write_text("""
    task_result_rules:
      - id: test_rule
        destination: ARCH
        escalation_level: none
        max_retries: 3
        retry_delay: 60
        phase_overrides:
          - phase: "phase1"
            destination: "CC"
            escalation_level: agent
          - phase: "phase2"
            max_retries: 5
            retry_delay: 120
    """)
    
    policy = load_policy(policy_file)
    assert policy is not None
    
    rule = policy.task_result_rules[0]
    assert len(rule.phase_overrides) == 2
    
    phase1_override = rule.phase_overrides[0]
    assert phase1_override.phase == "phase1"
    assert phase1_override.destination == "CC"
    assert phase1_override.escalation_level == EscalationLevel.AGENT
    
    phase2_override = rule.phase_overrides[1]
    assert phase2_override.phase == "phase2"
    assert phase2_override.max_retries == 5
    assert phase2_override.retry_delay == 120

def test_load_policy_with_complex_rules(tmp_path):
    """Test loading a policy with complex rule configurations."""
    policy_file = tmp_path / "complex_policy.yaml"
    policy_file.write_text("""
    task_result_rules:
      - id: complex_rule
        destination: ARCH
        escalation_level: none
        max_retries: 3
        retry_delay: 60
        conditions:
          - field: "content.status"
            operator: "in"
            value: ["completed", "failed"]
          - field: "content.progress"
            operator: ">="
            value: 100
    """)
    
    policy = load_policy(policy_file)
    assert policy is not None
    
    rule = policy.task_result_rules[0]
    assert len(rule.conditions) == 2
    
    status_condition = rule.conditions[0]
    assert status_condition.field == "content.status"
    assert status_condition.operator == "in"
    assert status_condition.value == ["completed", "failed"]
    
    progress_condition = rule.conditions[1]
    assert progress_condition.field == "content.progress"
    assert progress_condition.operator == ">="
    assert progress_condition.value == 100 