"""
Unit tests for Plan Context Engine and Conditional Evaluator.

Tests cover:
- Plan context management
- Safe expression evaluation  
- Conditional evaluation with when/unless
- Error handling and security
- Integration scenarios
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

from tools.arch.plan_utils import (
    PlanContextEngine,
    safe_eval_expression,
    evaluate_conditions,
    create_safe_eval_environment,
    log_conditional_skip,
    now_iso
)


class TestPlanContextEngine:
    """Test the PlanContextEngine class."""
    
    def test_initialization_empty(self):
        """Test initialization with no initial context."""
        engine = PlanContextEngine()
        assert engine.context == {}
        assert engine.evaluation_log == []
    
    def test_initialization_with_context(self):
        """Test initialization with initial context."""
        initial = {"mode": "production", "version": "1.0"}
        engine = PlanContextEngine(initial)
        assert engine.context == initial
        assert engine.evaluation_log == []
    
    def test_update_context(self):
        """Test updating context values."""
        engine = PlanContextEngine()
        engine.update_context("status", "running")
        engine.update_context("count", 42)
        
        assert engine.context["status"] == "running"
        assert engine.context["count"] == 42
    
    def test_update_from_task_result(self):
        """Test updating context from task execution result."""
        engine = PlanContextEngine()
        
        result = {
            "payload": {
                "content": {
                    "status": "completed",
                    "score": 0.95,
                    "context_updates": {
                        "data_processed": True,
                        "records_count": 1000
                    }
                }
            }
        }
        
        engine.update_from_task_result("TASK_001", result)
        
        assert engine.context["TASK_001_status"] == "completed"
        assert engine.context["TASK_001_score"] == 0.95
        assert engine.context["last_score"] == 0.95
        assert engine.context["TASK_001_completed"] == True
        assert engine.context["data_processed"] == True
        assert engine.context["records_count"] == 1000


class TestSafeEvalExpression:
    """Test the safe expression evaluation system."""
    
    def test_simple_expressions(self):
        """Test basic safe expressions."""
        context = {"x": 10, "y": 5}
        
        assert safe_eval_expression("x + y", context) == 15
        assert safe_eval_expression("x > y", context) == True
        assert safe_eval_expression("x == 10", context) == True
        assert safe_eval_expression("not (x < y)", context) == True
    
    def test_safe_functions(self):
        """Test allowed safe functions."""
        context = {"numbers": [1, 2, 3, 4, 5], "value": -10}
        
        assert safe_eval_expression("len(numbers)", context) == 5
        assert safe_eval_expression("max(numbers)", context) == 5
        assert safe_eval_expression("min(numbers)", context) == 1
        assert safe_eval_expression("abs(value)", context) == 10
        assert safe_eval_expression("round(3.7)", context) == 4
    
    def test_type_conversions(self):
        """Test safe type conversion functions."""
        context = {"text": "123", "number": 45.7}
        
        assert safe_eval_expression("int(text)", context) == 123
        assert safe_eval_expression("float(text)", context) == 123.0
        assert safe_eval_expression("str(number)", context) == "45.7"
        assert safe_eval_expression("bool(number)", context) == True
    
    def test_forbidden_operations(self):
        """Test that dangerous operations are blocked."""
        context = {"x": 10}
        
        # Import statements (caught as syntax error in eval mode)
        with pytest.raises(ValueError, match="Invalid expression syntax"):
            safe_eval_expression("import os", context)
        
        # Function calls (except allowed ones)
        with pytest.raises(ValueError, match="Forbidden function call"):
            safe_eval_expression("exec('print(1)')", context)
        
        # Attribute access
        with pytest.raises(ValueError, match="Forbidden operation"):
            safe_eval_expression("x.__class__", context)
        
        # Forbidden function calls
        with pytest.raises(ValueError, match="Forbidden function call"):
            safe_eval_expression("open('file.txt')", context)
    
    def test_syntax_errors(self):
        """Test handling of syntax errors."""
        context = {"x": 10}
        
        with pytest.raises(ValueError, match="Invalid expression syntax"):
            safe_eval_expression("x +", context)
        
        with pytest.raises(ValueError, match="Invalid expression syntax"):
            safe_eval_expression("if x > 5:", context)
    
    def test_runtime_errors(self):
        """Test handling of runtime errors."""
        context = {"x": 10}
        
        with pytest.raises(ValueError, match="Expression evaluation failed"):
            safe_eval_expression("x / 0", context)
        
        with pytest.raises(ValueError, match="Expression evaluation failed"):
            safe_eval_expression("undefined_variable", context)
    
    def test_empty_or_invalid_input(self):
        """Test handling of empty or invalid input."""
        context = {}
        
        with pytest.raises(ValueError, match="Expression must be a non-empty string"):
            safe_eval_expression("", context)
        
        with pytest.raises(ValueError, match="Expression must be a non-empty string"):
            safe_eval_expression(None, context)


class TestEvaluateConditions:
    """Test the conditional evaluation system."""
    
    def test_when_condition_only_pass(self):
        """Test when condition that should pass."""
        engine = PlanContextEngine({"score": 0.9, "mode": "production"})
        task = {
            "task_id": "TEST_TASK",
            "when": "score > 0.8"
        }
        
        should_execute, reason = evaluate_conditions(task, engine)
        
        assert should_execute == True
        assert "when='score > 0.8' -> True" in reason
        assert len(engine.evaluation_log) == 1
        assert engine.evaluation_log[0]["final_decision"] == True
    
    def test_when_condition_only_fail(self):
        """Test when condition that should fail."""
        engine = PlanContextEngine({"score": 0.5, "mode": "production"})
        task = {
            "task_id": "TEST_TASK", 
            "when": "score > 0.8"
        }
        
        should_execute, reason = evaluate_conditions(task, engine)
        
        assert should_execute == False
        assert "when condition failed" in reason
        assert len(engine.evaluation_log) == 1
        assert engine.evaluation_log[0]["final_decision"] == False
    
    def test_unless_condition_only_pass(self):
        """Test unless condition that should pass."""
        engine = PlanContextEngine({"mode": "production", "debug": False})
        task = {
            "task_id": "TEST_TASK",
            "unless": "mode == 'debug'"
        }
        
        should_execute, reason = evaluate_conditions(task, engine)
        
        assert should_execute == True
        assert "unless='mode == 'debug'' -> False" in reason
        assert len(engine.evaluation_log) == 1
        assert engine.evaluation_log[0]["final_decision"] == True
    
    def test_unless_condition_only_fail(self):
        """Test unless condition that should fail."""
        engine = PlanContextEngine({"mode": "debug", "debug": True})
        task = {
            "task_id": "TEST_TASK",
            "unless": "mode == 'debug'"
        }
        
        should_execute, reason = evaluate_conditions(task, engine)
        
        assert should_execute == False
        assert "unless condition failed" in reason
        assert len(engine.evaluation_log) == 1
        assert engine.evaluation_log[0]["final_decision"] == False
    
    def test_both_conditions_pass(self):
        """Test both when and unless conditions passing."""
        engine = PlanContextEngine({"score": 0.9, "mode": "production"})
        task = {
            "task_id": "TEST_TASK",
            "when": "score > 0.8",
            "unless": "mode == 'debug'"
        }
        
        should_execute, reason = evaluate_conditions(task, engine)
        
        assert should_execute == True
        assert "when='score > 0.8' -> True" in reason
        assert "unless='mode == 'debug'' -> False" in reason
        assert len(engine.evaluation_log) == 1
        assert engine.evaluation_log[0]["final_decision"] == True
    
    def test_when_passes_unless_fails(self):
        """Test when passes but unless fails."""
        engine = PlanContextEngine({"score": 0.9, "mode": "debug"})
        task = {
            "task_id": "TEST_TASK",
            "when": "score > 0.8",
            "unless": "mode == 'debug'"
        }
        
        should_execute, reason = evaluate_conditions(task, engine)
        
        assert should_execute == False
        assert "unless condition failed" in reason
        assert len(engine.evaluation_log) == 1
        assert engine.evaluation_log[0]["final_decision"] == False
    
    def test_no_conditions(self):
        """Test task with no conditions."""
        engine = PlanContextEngine({"score": 0.5})
        task = {
            "task_id": "TEST_TASK"
        }
        
        should_execute, reason = evaluate_conditions(task, engine)
        
        assert should_execute == True
        assert reason == "all conditions satisfied"
        assert len(engine.evaluation_log) == 1
        assert engine.evaluation_log[0]["final_decision"] == True
    
    def test_condition_evaluation_error(self):
        """Test handling of condition evaluation errors."""
        engine = PlanContextEngine({"score": 0.9})
        task = {
            "task_id": "TEST_TASK",
            "when": "undefined_variable > 0.8"
        }
        
        should_execute, reason = evaluate_conditions(task, engine)
        
        assert should_execute == False
        assert "condition evaluation error" in reason
        assert len(engine.evaluation_log) == 1
        assert engine.evaluation_log[0]["final_decision"] == False
        assert "error" in engine.evaluation_log[0]
    
    def test_complex_expressions(self):
        """Test complex conditional expressions."""
        engine = PlanContextEngine({
            "TASK_A_completed": True,
            "TASK_B_score": 0.85,
            "retry_count": 2,
            "max_retries": 3
        })
        
        task = {
            "task_id": "TEST_TASK",
            "when": "TASK_A_completed and TASK_B_score > 0.8",
            "unless": "retry_count >= max_retries"
        }
        
        should_execute, reason = evaluate_conditions(task, engine)
        
        assert should_execute == True
        assert len(engine.evaluation_log) == 1
        assert engine.evaluation_log[0]["final_decision"] == True


class TestLogConditionalSkip:
    """Test conditional skip logging functionality."""
    
    def test_log_conditional_skip(self):
        """Test logging a conditional skip."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logs_dir = Path(temp_dir)
            trace_id = "test-trace-123"
            
            # Create initial task log
            initial_log = {
                "trace_id": trace_id,
                "task_id": "TEST_TASK",
                "state_transitions": [
                    {
                        "from_state": "pending",
                        "to_state": "ready",
                        "timestamp": now_iso()
                    }
                ],
                "timestamps": {"created": now_iso()}
            }
            
            log_path = logs_dir / f"{trace_id}.json"
            with open(log_path, 'w') as f:
                json.dump(initial_log, f)
            
            # Log conditional skip
            reason = "when condition failed: 'score > 0.8' evaluated to False"
            log_conditional_skip(trace_id, logs_dir, "TEST_TASK", reason)
            
            # Verify log was updated
            with open(log_path, 'r') as f:
                updated_log = json.load(f)
            
            assert len(updated_log["state_transitions"]) == 2
            skip_transition = updated_log["state_transitions"][1]
            assert skip_transition["from_state"] == "ready"
            assert skip_transition["to_state"] == "skipped_due_to_condition"
            assert skip_transition["reason"] == reason
            assert "skipped" in updated_log["timestamps"]
            assert updated_log["execution_result"]["status"] == "skipped_due_to_condition"


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple components."""
    
    def test_task_dependency_with_conditions(self):
        """Test task with dependencies and conditional execution."""
        engine = PlanContextEngine()
        
        # Simulate first task completion
        result_1 = {
            "payload": {
                "content": {
                    "status": "completed",
                    "score": 0.95,
                    "context_updates": {
                        "data_quality": "high"
                    }
                }
            }
        }
        engine.update_from_task_result("VALIDATE_DATA", result_1)
        
        # Test second task that depends on first task's result
        task_2 = {
            "task_id": "PROCESS_DATA",
            "when": "VALIDATE_DATA_completed and data_quality == 'high'",
            "unless": "VALIDATE_DATA_score < 0.9"
        }
        
        should_execute, reason = evaluate_conditions(task_2, engine)
        
        assert should_execute == True
        assert engine.context["VALIDATE_DATA_completed"] == True
        assert engine.context["data_quality"] == "high"
        assert engine.context["last_score"] == 0.95
    
    def test_conditional_branching_scenario(self):
        """Test a conditional branching scenario."""
        engine = PlanContextEngine({"environment": "production", "user_role": "admin"})
        
        # Test admin-only task
        admin_task = {
            "task_id": "ADMIN_CLEANUP",
            "when": "user_role == 'admin'",
            "unless": "environment == 'development'"
        }
        
        should_execute, reason = evaluate_conditions(admin_task, engine)
        assert should_execute == True
        
        # Test debug task that shouldn't run in production
        debug_task = {
            "task_id": "DEBUG_LOGGING",
            "unless": "environment == 'production'"
        }
        
        should_execute, reason = evaluate_conditions(debug_task, engine)
        assert should_execute == False
    
    def test_error_recovery_scenario(self):
        """Test error recovery with conditional logic."""
        engine = PlanContextEngine({"retry_count": 0, "max_retries": 3})
        
        # Simulate task failure
        engine.update_context("last_error", "connection_timeout")
        engine.update_context("retry_count", 1)
        
        # Test retry task
        retry_task = {
            "task_id": "RETRY_OPERATION",
            "when": "retry_count < max_retries and last_error == 'connection_timeout'"
        }
        
        should_execute, reason = evaluate_conditions(retry_task, engine)
        assert should_execute == True
        
        # Test fallback task
        engine.update_context("retry_count", 3)
        fallback_task = {
            "task_id": "FALLBACK_OPERATION",
            "when": "retry_count >= max_retries"
        }
        
        should_execute, reason = evaluate_conditions(fallback_task, engine)
        assert should_execute == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])