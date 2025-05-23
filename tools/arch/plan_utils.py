import yaml
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Set, Optional
from jsonschema import validate, ValidationError
from collections import defaultdict, deque
from dataclasses import dataclass
import time

@dataclass
class TaskNode:
    """Represents a task node in the execution DAG."""
    task_id: str
    agent: str
    task_type: str
    description: str
    priority: str
    dependencies: List[str]
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass 
class ExecutionDAG:
    """Represents a directed acyclic graph of task execution."""
    nodes: Dict[str, TaskNode]
    edges: Dict[str, List[str]]  # task_id -> list of dependent task_ids
    reverse_edges: Dict[str, List[str]]  # task_id -> list of prerequisite task_ids
    root_nodes: List[str]  # nodes with no dependencies
    leaf_nodes: List[str]  # nodes with no dependents
    execution_order: List[str]  # topologically sorted task order
    
    def __post_init__(self):
        self._validate_structure()
    
    def _validate_structure(self):
        """Validate DAG structure and detect cycles."""
        # Verify all referenced dependencies exist
        for node_id, node in self.nodes.items():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    raise ValueError(f"Task '{node_id}' depends on non-existent task '{dep}'")
        
        # Detect cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_id: str) -> bool:
            if node_id in rec_stack:
                return True
            if node_id in visited:
                return False
            
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for dependent in self.edges.get(node_id, []):
                if has_cycle(dependent):
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    raise ValueError(f"Cycle detected in execution plan involving task '{node_id}'")
    
    def get_ready_tasks(self, completed_tasks: Set[str]) -> List[str]:
        """Get tasks that are ready to execute (all dependencies completed)."""
        ready = []
        for task_id, node in self.nodes.items():
            if task_id in completed_tasks:
                continue
            if all(dep in completed_tasks for dep in node.dependencies):
                ready.append(task_id)
        return ready
    
    def get_execution_layers(self) -> List[List[str]]:
        """Get tasks grouped by execution layers (can run in parallel)."""
        layers = []
        completed = set()
        
        while len(completed) < len(self.nodes):
            current_layer = self.get_ready_tasks(completed)
            if not current_layer:
                raise ValueError("Unable to determine execution order - possible circular dependency")
            layers.append(current_layer)
            completed.update(current_layer)
        
        return layers

class DAGValidationError(Exception):
    """Custom exception for DAG validation errors."""
    pass

# Load and validate a plan YAML file against PLAN_SCHEMA.json
def load_and_validate_plan(plan_path: Path, schema_path: Path) -> Dict[str, Any]:
    with open(plan_path, 'r') as f:
        plan_data = yaml.safe_load(f)
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    try:
        validate(instance=plan_data, schema=schema)
    except ValidationError as e:
        raise ValueError(f"Plan validation failed: {e.message}")
    return plan_data

# Generate a unique trace_id for a task
def generate_trace_id(plan_id: str, task_index: int) -> str:
    return f"{plan_id}-{task_index}-{uuid.uuid4().hex[:8]}"

# Get current ISO timestamp
def now_iso() -> str:
    return datetime.utcnow().isoformat() + 'Z'

# Write a message to an agent's inbox
def write_to_inbox(agent: str, message: Dict[str, Any], postbox_root: Path) -> None:
    inbox_path = postbox_root / agent / 'inbox.json'
    inbox_path.parent.mkdir(parents=True, exist_ok=True)
    if inbox_path.exists():
        with open(inbox_path, 'r') as f:
            inbox = json.load(f)
    else:
        inbox = []
    inbox.append(message)
    with open(inbox_path, 'w') as f:
        json.dump(inbox, f, indent=2)

# Enhanced DAG-aware task logging
def create_enhanced_task_log(trace_id: str, plan_id: str, task_node: TaskNode, 
                           execution_layer: int, parallel_tasks: List[str],
                           depth: int) -> Dict[str, Any]:
    """Create an enhanced task log structure with DAG metadata."""
    now = now_iso()
    return {
        "trace_id": trace_id,
        "plan_id": plan_id,
        "task_id": task_node.task_id,
        "agent": task_node.agent,
        "execution_metadata": {
            "execution_layer": execution_layer,
            "dependencies": task_node.dependencies,
            "task_type": task_node.task_type,
            "priority": task_node.priority,
            "parallel_tasks": parallel_tasks,
            "depth": depth
        },
        "state_transitions": [
            {
                "from_state": "pending",
                "to_state": "waiting",
                "timestamp": now,
                "reason": "Task created, waiting for dependencies"
            }
        ],
        "timestamps": {
            "created": now,
            "last_updated": now
        },
        "execution_result": {},
        "retry_history": [],
        "task_content": {
            "action": task_node.content.get("action"),
            "parameters": task_node.content.get("parameters", {}),
            "requirements": task_node.content.get("requirements", []),
            "input_files": task_node.content.get("input_files", []),
            "output_files": task_node.content.get("output_files", [])
        }
    }

def update_task_log_state(trace_id: str, logs_dir: Path, from_state: str, 
                         to_state: str, reason: str = None, retry_count: int = 0) -> None:
    """Update task log with state transition."""
    log_path = logs_dir / f"{trace_id}.json"
    
    if not log_path.exists():
        raise FileNotFoundError(f"Task log not found: {log_path}")
    
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    now = now_iso()
    transition = {
        "from_state": from_state,
        "to_state": to_state,
        "timestamp": now
    }
    
    if reason:
        transition["reason"] = reason
    if retry_count > 0:
        transition["retry_count"] = retry_count
    
    log_data["state_transitions"].append(transition)
    log_data["timestamps"]["last_updated"] = now
    
    # Update specific timestamps
    if to_state == "running":
        log_data["timestamps"]["started"] = now
    elif to_state in ["completed", "failed", "timeout"]:
        log_data["timestamps"]["completed"] = now
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)

def update_task_log_result(trace_id: str, logs_dir: Path, result: Dict[str, Any],
                          duration_sec: float = None) -> None:
    """Update task log with execution result."""
    log_path = logs_dir / f"{trace_id}.json"
    
    if not log_path.exists():
        raise FileNotFoundError(f"Task log not found: {log_path}")
    
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    payload_content = result.get('payload', {}).get('content', {})
    
    log_data["execution_result"] = {
        "status": payload_content.get('status', 'unknown'),
        "score": payload_content.get('score'),
        "duration_sec": duration_sec or payload_content.get('duration_sec'),
        "output_files": payload_content.get('output_files', []),
        "error_message": payload_content.get('error_message'),
        "mcp_response": result
    }
    
    log_data["timestamps"]["last_updated"] = now_iso()
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)

def add_retry_to_task_log(trace_id: str, logs_dir: Path, attempt: int, 
                         result: str, error_message: str = None, duration_sec: float = None) -> None:
    """Add retry attempt to task log history."""
    log_path = logs_dir / f"{trace_id}.json"
    
    if not log_path.exists():
        raise FileNotFoundError(f"Task log not found: {log_path}")
    
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    retry_entry = {
        "attempt": attempt,
        "timestamp": now_iso(),
        "result": result
    }
    
    if error_message:
        retry_entry["error_message"] = error_message
    if duration_sec:
        retry_entry["duration_sec"] = duration_sec
    
    log_data["retry_history"].append(retry_entry)
    log_data["timestamps"]["last_updated"] = now_iso()
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)

# Write a log entry for a task execution (legacy function for backwards compatibility)
def write_task_log(trace_id: str, log_data: Dict[str, Any], logs_dir: Path) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"{trace_id}.json"
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)

def build_execution_dag(plan_dict: Dict[str, Any]) -> ExecutionDAG:
    """
    Build an execution DAG from a validated plan dictionary.
    
    Args:
        plan_dict: Validated plan data from YAML
        
    Returns:
        ExecutionDAG: Complete DAG with validation and execution ordering
        
    Raises:
        DAGValidationError: If the plan contains invalid dependencies or cycles
    """
    try:
        tasks = plan_dict.get('tasks', [])
        if not tasks:
            raise DAGValidationError("Plan contains no tasks")
        
        # Build task nodes
        nodes = {}
        for task_data in tasks:
            task_id = task_data['task_id']
            dependencies = task_data.get('dependencies', [])
            
            # Extract metadata from task
            metadata = {
                'deadline': task_data.get('deadline'),
                'max_retries': task_data.get('max_retries', 0),
                'timeout': task_data.get('timeout'),
                'retry_strategy': task_data.get('retry_strategy'),
                'retry_delay': task_data.get('retry_delay'),
                'fallback_agent': task_data.get('fallback_agent'),
                'conditions': task_data.get('conditions'),
                'notifications': task_data.get('notifications', {}),
                'cost_center': task_data.get('metadata', {}).get('cost_center'),
                'compliance_required': task_data.get('metadata', {}).get('compliance_required', False)
            }
            
            node = TaskNode(
                task_id=task_id,
                agent=task_data['agent'],
                task_type=task_data['task_type'],
                description=task_data['description'],
                priority=task_data.get('priority', 'medium'),
                dependencies=dependencies,
                content=task_data.get('content', {}),
                metadata=metadata
            )
            nodes[task_id] = node
        
        # Validate all dependencies exist before building edges
        for task_id, node in nodes.items():
            for dep in node.dependencies:
                if dep not in nodes:
                    raise DAGValidationError(f"Task '{task_id}' depends on non-existent task '{dep}'")
        
        # Build edges (forward and reverse)
        edges = defaultdict(list)  # task_id -> dependents
        reverse_edges = defaultdict(list)  # task_id -> prerequisites
        
        for task_id, node in nodes.items():
            for dep in node.dependencies:
                edges[dep].append(task_id)
                reverse_edges[task_id].append(dep)
        
        # Find root and leaf nodes
        root_nodes = [task_id for task_id, node in nodes.items() if not node.dependencies]
        leaf_nodes = [task_id for task_id in nodes.keys() if not edges[task_id]]
        
        # Generate topological sort for execution order
        execution_order = _topological_sort(nodes, reverse_edges)
        
        dag = ExecutionDAG(
            nodes=nodes,
            edges=dict(edges),
            reverse_edges=dict(reverse_edges),
            root_nodes=root_nodes,
            leaf_nodes=leaf_nodes,
            execution_order=execution_order
        )
        
        return dag
        
    except Exception as e:
        raise DAGValidationError(f"Failed to build execution DAG: {str(e)}")

def _topological_sort(nodes: Dict[str, TaskNode], reverse_edges: Dict[str, List[str]]) -> List[str]:
    """
    Perform topological sort to determine execution order.
    
    Returns:
        List[str]: Task IDs in execution order
    """
    # Kahn's algorithm for topological sorting
    in_degree = {task_id: len(reverse_edges.get(task_id, [])) for task_id in nodes}
    queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
    result = []
    
    while queue:
        current = queue.popleft()
        result.append(current)
        
        # For each node that depends on current, reduce its in-degree
        for task_id, node in nodes.items():
            if current in node.dependencies:
                in_degree[task_id] -= 1
                if in_degree[task_id] == 0:
                    queue.append(task_id)
    
    if len(result) != len(nodes):
        raise DAGValidationError("Cycle detected during topological sort")
    
    return result

def validate_dag_integrity(dag: ExecutionDAG) -> Dict[str, Any]:
    """
    Perform comprehensive validation of DAG integrity.
    
    Returns:
        Dict containing validation results and statistics
    """
    validation_results = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'statistics': {
            'total_tasks': len(dag.nodes),
            'root_tasks': len(dag.root_nodes),
            'leaf_tasks': len(dag.leaf_nodes),
            'max_depth': 0,
            'parallelizable_layers': len(dag.get_execution_layers()),
            'agents_involved': len(set(node.agent for node in dag.nodes.values()))
        }
    }
    
    try:
        # Check for isolated nodes
        all_referenced = set()
        for node in dag.nodes.values():
            all_referenced.update(node.dependencies)
        for dependents in dag.edges.values():
            all_referenced.update(dependents)
        
        isolated = set(dag.nodes.keys()) - all_referenced - set(dag.root_nodes)
        if isolated:
            validation_results['warnings'].append(f"Isolated tasks found: {isolated}")
        
        # Calculate max depth
        def calculate_depth(task_id: str, memo: Dict[str, int] = {}) -> int:
            if task_id in memo:
                return memo[task_id]
            
            deps = dag.nodes[task_id].dependencies
            if not deps:
                memo[task_id] = 0
                return 0
            
            max_dep_depth = max(calculate_depth(dep, memo) for dep in deps)
            memo[task_id] = max_dep_depth + 1
            return memo[task_id]
        
        validation_results['statistics']['max_depth'] = max(
            calculate_depth(task_id) for task_id in dag.nodes
        )
        
    except Exception as e:
        validation_results['is_valid'] = False
        validation_results['errors'].append(f"Validation error: {str(e)}")
    
    return validation_results

# Central execution trace logging
class ExecutionTracer:
    """Manages central execution trace logging for plan execution."""
    
    def __init__(self, plan_dict: Dict[str, Any], dag: ExecutionDAG, logs_dir: Path):
        self.plan_dict = plan_dict
        self.dag = dag
        self.logs_dir = logs_dir
        self.execution_id = f"exec-{uuid.uuid4()}"
        self.start_time = time.time()
        self.timeline = []
        
        # Initialize execution trace
        self.trace_data = self._create_initial_trace()
        
    def _create_initial_trace(self) -> Dict[str, Any]:
        """Create the initial execution trace structure."""
        metadata = self.plan_dict.get('metadata', {})
        layers = self.dag.get_execution_layers()
        
        return {
            "plan_id": metadata.get('plan_id', 'unknown'),
            "execution_id": self.execution_id,
            "plan_metadata": {
                "version": metadata.get('version', '1.0.0'),
                "description": metadata.get('description', ''),
                "total_tasks": len(self.dag.nodes),
                "priority": metadata.get('priority', 'medium'),
                "author": metadata.get('author'),
                "environment": metadata.get('environment', 'development')
            },
            "dag_analysis": {
                "execution_layers": [
                    {"layer": i, "tasks": layer_tasks} 
                    for i, layer_tasks in enumerate(layers)
                ],
                "critical_path": self._calculate_critical_path(),
                "parallelizable_tasks": max(len(layer) for layer in layers) if layers else 0,
                "total_depth": len(layers),
                "agents_involved": list(set(node.agent for node in self.dag.nodes.values()))
            },
            "execution_timeline": [],
            "summary": {
                "start_time": now_iso(),
                "status": "running",
                "tasks_completed": 0,
                "tasks_failed": 0,
                "tasks_timeout": 0,
                "total_retries": 0
            }
        }
    
    def _calculate_critical_path(self) -> List[str]:
        """Calculate the critical path through the DAG."""
        # Use execution order as a proxy for critical path
        # In a real implementation, you'd want to calculate actual longest path
        return self.dag.execution_order
    
    def log_event(self, event_type: str, task_id: str = None, agent: str = None, 
                  execution_layer: int = None, details: Dict[str, Any] = None, 
                  trace_id: str = None) -> None:
        """Log an execution event to the timeline."""
        event = {
            "timestamp": now_iso(),
            "event_type": event_type,
            "task_id": task_id
        }
        
        if agent:
            event["agent"] = agent
        if execution_layer is not None:
            event["execution_layer"] = execution_layer
        if details:
            event["details"] = details
        if trace_id:
            event["trace_id"] = trace_id
            
        self.trace_data["execution_timeline"].append(event)
        self._update_summary(event_type)
    
    def _update_summary(self, event_type: str) -> None:
        """Update execution summary based on event type."""
        summary = self.trace_data["summary"]
        
        if event_type == "task_completed":
            summary["tasks_completed"] += 1
        elif event_type == "task_failed":
            summary["tasks_failed"] += 1
        elif event_type == "task_timeout":
            summary["tasks_timeout"] += 1
        elif event_type == "task_retry":
            summary["total_retries"] += 1
    
    def finalize_trace(self, final_status: str) -> None:
        """Finalize the execution trace and write to disk."""
        end_time = time.time()
        
        self.trace_data["summary"].update({
            "end_time": now_iso(),
            "total_duration_sec": end_time - self.start_time,
            "status": final_status
        })
        
        # Calculate average task score if we have completed tasks
        completed_tasks = self.trace_data["summary"]["tasks_completed"]
        if completed_tasks > 0:
            # This would need to be calculated from individual task logs
            # For now, we'll leave it as placeholder
            self.trace_data["summary"]["avg_task_score"] = None
        
        # Calculate parallelism achieved
        # This would require analyzing the timeline for concurrent tasks
        self.trace_data["summary"]["parallelism_achieved"] = None
        
        # Write trace to disk
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        trace_path = self.logs_dir / f"execution_trace_{self.execution_id}.json"
        
        with open(trace_path, 'w') as f:
            json.dump(self.trace_data, f, indent=2)
    
    def get_execution_id(self) -> str:
        """Get the execution ID for this trace."""
        return self.execution_id