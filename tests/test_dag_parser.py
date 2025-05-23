import pytest
import json
from pathlib import Path
from typing import Dict, Any

# Import our DAG classes and functions
import sys
sys.path.append(str(Path(__file__).parent.parent))

from tools.arch.plan_utils import (
    TaskNode, ExecutionDAG, DAGValidationError,
    build_execution_dag, validate_dag_integrity
)

class TestDAGParser:
    """Comprehensive test suite for DAG parser functionality."""
    
    def test_simple_linear_plan(self):
        """Test basic linear task dependencies: A -> B -> C"""
        plan_dict = {
            'plan_id': 'test-linear',
            'tasks': [
                {
                    'task_id': 'TASK_A',
                    'agent': 'CA',
                    'task_type': 'data_processing',
                    'description': 'First task',
                    'dependencies': []
                },
                {
                    'task_id': 'TASK_B', 
                    'agent': 'CC',
                    'task_type': 'validation',
                    'description': 'Second task',
                    'dependencies': ['TASK_A']
                },
                {
                    'task_id': 'TASK_C',
                    'agent': 'WA',
                    'task_type': 'report_generation',
                    'description': 'Third task',
                    'dependencies': ['TASK_B']
                }
            ]
        }
        
        dag = build_execution_dag(plan_dict)
        
        assert len(dag.nodes) == 3
        assert dag.root_nodes == ['TASK_A']
        assert dag.leaf_nodes == ['TASK_C']
        assert dag.execution_order == ['TASK_A', 'TASK_B', 'TASK_C']
        
        # Test execution layers
        layers = dag.get_execution_layers()
        assert len(layers) == 3
        assert layers[0] == ['TASK_A']
        assert layers[1] == ['TASK_B']
        assert layers[2] == ['TASK_C']
    
    def test_parallel_tasks(self):
        """Test parallel task execution: A -> [B, C] -> D"""
        plan_dict = {
            'plan_id': 'test-parallel',
            'tasks': [
                {
                    'task_id': 'TASK_A',
                    'agent': 'CA',
                    'task_type': 'data_processing',
                    'description': 'Root task',
                    'dependencies': []
                },
                {
                    'task_id': 'TASK_B',
                    'agent': 'CC',
                    'task_type': 'validation',
                    'description': 'Parallel task 1',
                    'dependencies': ['TASK_A']
                },
                {
                    'task_id': 'TASK_C',
                    'agent': 'WA',
                    'task_type': 'validation',
                    'description': 'Parallel task 2',
                    'dependencies': ['TASK_A']
                },
                {
                    'task_id': 'TASK_D',
                    'agent': 'CA',
                    'task_type': 'report_generation',
                    'description': 'Final task',
                    'dependencies': ['TASK_B', 'TASK_C']
                }
            ]
        }
        
        dag = build_execution_dag(plan_dict)
        
        assert len(dag.nodes) == 4
        assert dag.root_nodes == ['TASK_A']
        assert dag.leaf_nodes == ['TASK_D']
        
        # Test execution layers - B and C should be in same layer
        layers = dag.get_execution_layers()
        assert len(layers) == 3
        assert layers[0] == ['TASK_A']
        assert set(layers[1]) == {'TASK_B', 'TASK_C'}
        assert layers[2] == ['TASK_D']
        
        # Test ready tasks
        ready = dag.get_ready_tasks(set())
        assert ready == ['TASK_A']
        
        ready = dag.get_ready_tasks({'TASK_A'})
        assert set(ready) == {'TASK_B', 'TASK_C'}
        
        ready = dag.get_ready_tasks({'TASK_A', 'TASK_B', 'TASK_C'})
        assert ready == ['TASK_D']
    
    def test_cycle_detection(self):
        """Test cycle detection in dependencies"""
        plan_dict = {
            'plan_id': 'test-cycle',
            'tasks': [
                {
                    'task_id': 'TASK_A',
                    'agent': 'CA',
                    'task_type': 'data_processing',
                    'description': 'Task A',
                    'dependencies': ['TASK_C']  # Creates cycle: A -> C -> B -> A
                },
                {
                    'task_id': 'TASK_B',
                    'agent': 'CC',
                    'task_type': 'validation',
                    'description': 'Task B',
                    'dependencies': ['TASK_A']
                },
                {
                    'task_id': 'TASK_C',
                    'agent': 'WA',
                    'task_type': 'validation',
                    'description': 'Task C',
                    'dependencies': ['TASK_B']
                }
            ]
        }
        
        with pytest.raises(DAGValidationError, match="Failed to build execution DAG"):
            build_execution_dag(plan_dict)
    
    def test_self_dependency(self):
        """Test self-dependency detection"""
        plan_dict = {
            'plan_id': 'test-self-dep',
            'tasks': [
                {
                    'task_id': 'TASK_A',
                    'agent': 'CA',
                    'task_type': 'data_processing',
                    'description': 'Self-dependent task',
                    'dependencies': ['TASK_A']  # Self-dependency
                }
            ]
        }
        
        with pytest.raises(DAGValidationError):
            build_execution_dag(plan_dict)
    
    def test_missing_dependency(self):
        """Test missing dependency detection"""
        plan_dict = {
            'plan_id': 'test-missing-dep',
            'tasks': [
                {
                    'task_id': 'TASK_A',
                    'agent': 'CA',
                    'task_type': 'data_processing',
                    'description': 'Task with missing dependency',
                    'dependencies': ['NONEXISTENT_TASK']
                }
            ]
        }
        
        with pytest.raises(DAGValidationError, match="non-existent task"):
            build_execution_dag(plan_dict)
    
    def test_complex_dag(self):
        """Test complex DAG with multiple paths and convergence points"""
        plan_dict = {
            'plan_id': 'test-complex',
            'tasks': [
                {
                    'task_id': 'VALIDATE_INPUT',
                    'agent': 'CA',
                    'task_type': 'validation',
                    'description': 'Validate input data',
                    'dependencies': []
                },
                {
                    'task_id': 'TRANSFORM_DATA',
                    'agent': 'CA',
                    'task_type': 'data_processing',
                    'description': 'Transform data',
                    'dependencies': ['VALIDATE_INPUT']
                },
                {
                    'task_id': 'QUALITY_CHECK',
                    'agent': 'CC',
                    'task_type': 'validation',
                    'description': 'Quality assessment',
                    'dependencies': ['TRANSFORM_DATA']
                },
                {
                    'task_id': 'GENERATE_REPORT',
                    'agent': 'WA',
                    'task_type': 'report_generation',
                    'description': 'Generate business report',
                    'dependencies': ['TRANSFORM_DATA', 'QUALITY_CHECK']
                },
                {
                    'task_id': 'HEALTH_CHECK',
                    'agent': 'CC',
                    'task_type': 'system_check',
                    'description': 'System health check',
                    'dependencies': []
                },
                {
                    'task_id': 'FINAL_VALIDATION',
                    'agent': 'CA',
                    'task_type': 'validation',
                    'description': 'Final validation',
                    'dependencies': ['GENERATE_REPORT', 'HEALTH_CHECK']
                }
            ]
        }
        
        dag = build_execution_dag(plan_dict)
        
        assert len(dag.nodes) == 6
        assert set(dag.root_nodes) == {'VALIDATE_INPUT', 'HEALTH_CHECK'}
        assert dag.leaf_nodes == ['FINAL_VALIDATION']
        
        # Verify execution order respects dependencies
        order = dag.execution_order
        assert order.index('VALIDATE_INPUT') < order.index('TRANSFORM_DATA')
        assert order.index('TRANSFORM_DATA') < order.index('QUALITY_CHECK')
        assert order.index('TRANSFORM_DATA') < order.index('GENERATE_REPORT')
        assert order.index('QUALITY_CHECK') < order.index('GENERATE_REPORT')
        assert order.index('GENERATE_REPORT') < order.index('FINAL_VALIDATION')
        assert order.index('HEALTH_CHECK') < order.index('FINAL_VALIDATION')
    
    def test_empty_plan(self):
        """Test handling of empty plan"""
        plan_dict = {'plan_id': 'test-empty', 'tasks': []}
        
        with pytest.raises(DAGValidationError, match="Plan contains no tasks"):
            build_execution_dag(plan_dict)
    
    def test_task_node_metadata(self):
        """Test TaskNode metadata extraction"""
        plan_dict = {
            'plan_id': 'test-metadata',
            'tasks': [
                {
                    'task_id': 'TASK_WITH_METADATA',
                    'agent': 'CA',
                    'task_type': 'data_processing',
                    'description': 'Task with complete metadata',
                    'priority': 'high',
                    'dependencies': [],
                    'deadline': '2025-05-22T10:00:00Z',
                    'max_retries': 3,
                    'timeout': '30m',
                    'retry_strategy': 'exponential_backoff',
                    'retry_delay': '1m',
                    'fallback_agent': 'CC',
                    'conditions': {'when': 'ready'},
                    'notifications': {'on_failure': ['admin@example.com']},
                    'metadata': {
                        'cost_center': 'data-ops',
                        'compliance_required': True
                    },
                    'content': {
                        'action': 'process_data',
                        'parameters': {'input_file': '/data/input.csv'}
                    }
                }
            ]
        }
        
        dag = build_execution_dag(plan_dict)
        task = dag.nodes['TASK_WITH_METADATA']
        
        assert task.priority == 'high'
        assert task.metadata['deadline'] == '2025-05-22T10:00:00Z'
        assert task.metadata['max_retries'] == 3
        assert task.metadata['timeout'] == '30m'
        assert task.metadata['retry_strategy'] == 'exponential_backoff'
        assert task.metadata['fallback_agent'] == 'CC'
        assert task.metadata['cost_center'] == 'data-ops'
        assert task.metadata['compliance_required'] == True
        assert task.content['action'] == 'process_data'
    
    def test_dag_integrity_validation(self):
        """Test comprehensive DAG integrity validation"""
        plan_dict = {
            'plan_id': 'test-integrity',
            'tasks': [
                {
                    'task_id': 'ROOT_1',
                    'agent': 'CA',
                    'task_type': 'data_processing',
                    'description': 'Root task 1',
                    'dependencies': []
                },
                {
                    'task_id': 'ROOT_2',
                    'agent': 'CC',
                    'task_type': 'validation',
                    'description': 'Root task 2',
                    'dependencies': []
                },
                {
                    'task_id': 'MIDDLE',
                    'agent': 'WA',
                    'task_type': 'transformation',
                    'description': 'Middle task',
                    'dependencies': ['ROOT_1']
                },
                {
                    'task_id': 'LEAF',
                    'agent': 'CA',
                    'task_type': 'report_generation',
                    'description': 'Leaf task',
                    'dependencies': ['MIDDLE', 'ROOT_2']
                }
            ]
        }
        
        dag = build_execution_dag(plan_dict)
        validation = validate_dag_integrity(dag)
        
        assert validation['is_valid'] == True
        assert validation['statistics']['total_tasks'] == 4
        assert validation['statistics']['root_tasks'] == 2
        assert validation['statistics']['leaf_tasks'] == 1
        assert validation['statistics']['max_depth'] == 2
        assert validation['statistics']['parallelizable_layers'] == 3
        assert validation['statistics']['agents_involved'] == 3
    
    def test_isolated_nodes_warning(self):
        """Test warning for isolated nodes"""
        plan_dict = {
            'plan_id': 'test-isolated',
            'tasks': [
                {
                    'task_id': 'CONNECTED_1',
                    'agent': 'CA',
                    'task_type': 'data_processing',
                    'description': 'Connected task 1',
                    'dependencies': []
                },
                {
                    'task_id': 'CONNECTED_2',
                    'agent': 'CC',
                    'task_type': 'validation',
                    'description': 'Connected task 2',
                    'dependencies': ['CONNECTED_1']
                }
            ]
        }
        
        dag = build_execution_dag(plan_dict)
        validation = validate_dag_integrity(dag)
        
        # No isolated nodes in this case since all tasks are in the main flow
        assert validation['is_valid'] == True
        assert len(validation['warnings']) == 0

    def test_real_sample_plan(self):
        """Test with actual sample plan structure"""
        # Simplified version of the sample plan for testing
        plan_dict = {
            'plan_id': 'sample-test',
            'tasks': [
                {
                    'task_id': 'VALIDATE_INPUT_DATA',
                    'agent': 'CA',
                    'task_type': 'validation',
                    'description': 'Validate input data',
                    'dependencies': []
                },
                {
                    'task_id': 'TRANSFORM_DATA',
                    'agent': 'CA',
                    'task_type': 'data_processing',
                    'description': 'Transform validated data',
                    'dependencies': ['VALIDATE_INPUT_DATA']
                },
                {
                    'task_id': 'ASSESS_DATA_QUALITY',
                    'agent': 'CA',
                    'task_type': 'validation',
                    'description': 'Assess data quality',
                    'dependencies': ['TRANSFORM_DATA']
                },
                {
                    'task_id': 'GENERATE_BUSINESS_REPORT',
                    'agent': 'WA',
                    'task_type': 'report_generation',
                    'description': 'Generate business report',
                    'dependencies': ['TRANSFORM_DATA', 'ASSESS_DATA_QUALITY']
                }
            ]
        }
        
        dag = build_execution_dag(plan_dict)
        
        assert len(dag.nodes) == 4
        assert dag.root_nodes == ['VALIDATE_INPUT_DATA']
        assert dag.leaf_nodes == ['GENERATE_BUSINESS_REPORT']
        
        # Verify the diamond dependency pattern works correctly
        layers = dag.get_execution_layers()
        assert layers[0] == ['VALIDATE_INPUT_DATA']
        assert layers[1] == ['TRANSFORM_DATA']
        assert layers[2] == ['ASSESS_DATA_QUALITY']
        assert layers[3] == ['GENERATE_BUSINESS_REPORT']
        
        # Test that GENERATE_BUSINESS_REPORT waits for both dependencies
        ready = dag.get_ready_tasks({'VALIDATE_INPUT_DATA', 'TRANSFORM_DATA'})
        assert ready == ['ASSESS_DATA_QUALITY']
        
        ready = dag.get_ready_tasks({'VALIDATE_INPUT_DATA', 'TRANSFORM_DATA', 'ASSESS_DATA_QUALITY'})
        assert ready == ['GENERATE_BUSINESS_REPORT']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])