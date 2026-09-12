"""
In-memory Directed Acyclic Graph (DAG) TaskGraph domain model.
"""

from collections import defaultdict, deque

from src.domain.exceptions import TaskCycleError, TaskDependencyError, TaskNotFoundError
from src.domain.task import BlockReason, Task, TaskStatus
from src.domain.task_dependency import DependencyStatus, TaskDependency


class TaskGraph:
    """
    Deterministic Task Dependency Graph model providing node/edge management,
    cycle detection, topological sorting, predecessor/successor lookups,
    and readiness/blocking evaluation.
    """

    def __init__(self) -> None:
        self.tasks: dict[str, Task] = {}
        self.dependencies: dict[str, TaskDependency] = {}
        # adjacency lists:
        # predecessor -> successors (outgoing edges)
        self._adj_out: dict[str, set[str]] = defaultdict(set)
        # successor -> predecessors (incoming edges)
        self._adj_in: dict[str, set[str]] = defaultdict(set)

    def add_task(self, task: Task) -> None:
        """Add a Task node to the graph."""
        self.tasks[task.id] = task

    def get_task(self, task_id: str) -> Task:
        """Get a Task node or raise TaskNotFoundError."""
        if task_id not in self.tasks:
            raise TaskNotFoundError(task_id)
        return self.tasks[task_id]

    def add_dependency(self, dependency: TaskDependency) -> None:
        """
        Add a TaskDependency edge to the graph.
        Validates node existence, self-dependency, duplicate edges, and cycle creation.
        """
        pred_id = dependency.predecessor_task_id
        succ_id = dependency.successor_task_id

        if pred_id not in self.tasks:
            raise TaskNotFoundError(pred_id)
        if succ_id not in self.tasks:
            raise TaskNotFoundError(succ_id)
        if pred_id == succ_id:
            raise TaskDependencyError(f"Task '{pred_id}' cannot depend on itself.")

        if dependency.id in self.dependencies:
            return

        # Pre-persistence cycle detection check:
        # If there is already a path from succ_id to pred_id,
        # adding pred_id -> succ_id creates a cycle.
        cycle_path = self._find_path(succ_id, pred_id)
        if cycle_path:
            full_cycle = [pred_id] + cycle_path
            path_str = " -> ".join(full_cycle)
            raise TaskCycleError(
                f"Cannot add dependency '{pred_id}' -> '{succ_id}': "
                f"creates a dependency cycle: {path_str}."
            )

        self.dependencies[dependency.id] = dependency
        if dependency.status == DependencyStatus.ACTIVE:
            self._adj_out[pred_id].add(succ_id)
            self._adj_in[succ_id].add(pred_id)

    def remove_dependency(self, dependency_id: str) -> None:
        """Remove a dependency edge from the graph."""
        if dependency_id not in self.dependencies:
            return
        dep = self.dependencies.pop(dependency_id)
        pred_id = dep.predecessor_task_id
        succ_id = dep.successor_task_id
        self._adj_out[pred_id].discard(succ_id)
        self._adj_in[succ_id].discard(pred_id)

    def get_predecessors(self, task_id: str) -> list[Task]:
        """Return tasks that predecessor_task_id -> task_id."""
        if task_id not in self.tasks:
            raise TaskNotFoundError(task_id)
        pred_ids = self._adj_in.get(task_id, set())
        return [self.tasks[pid] for pid in pred_ids if pid in self.tasks]

    def get_successors(self, task_id: str) -> list[Task]:
        """Return tasks that task_id -> successor_task_id."""
        if task_id not in self.tasks:
            raise TaskNotFoundError(task_id)
        succ_ids = self._adj_out.get(task_id, set())
        return [self.tasks[sid] for sid in succ_ids if sid in self.tasks]

    def _find_path(self, start_id: str, target_id: str) -> list[str] | None:
        """Find a directed path from start_id to target_id using BFS."""
        if start_id == target_id:
            return [start_id]
        visited: set[str] = set()
        queue: deque[list[str]] = deque([[start_id]])
        while queue:
            path = queue.popleft()
            curr = path[-1]
            if curr == target_id:
                return path
            if curr not in visited:
                visited.add(curr)
                for next_id in self._adj_out.get(curr, set()):
                    if next_id not in visited:
                        queue.append(path + [next_id])
        return None

    def detect_cycle(self) -> list[str] | None:
        """
        Detect if the current graph contains any cycle.
        Returns the cycle path as a list of task_ids if found, else None.
        """
        visited: set[str] = set()
        rec_stack: set[str] = set()
        cycle_path: list[str] = []

        def dfs(node_id: str, path: list[str]) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            for neighbor in self._adj_out.get(node_id, set()):
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    cycle_start_idx = path.index(neighbor)
                    cycle_path.extend(path[cycle_start_idx:] + [neighbor])
                    return True

            rec_stack.remove(node_id)
            path.pop()
            return False

        for task_id in self.tasks:
            if task_id not in visited and dfs(task_id, []):
                return cycle_path
        return None

    def get_topological_sort(self) -> list[Task]:
        """
        Return tasks sorted in topological order using Kahn's algorithm.
        Raises TaskCycleError if a cycle is present.
        """
        in_degree: dict[str, int] = {tid: 0 for tid in self.tasks}
        for u in self._adj_out:
            for v in self._adj_out[u]:
                if v in in_degree:
                    in_degree[v] += 1

        queue: deque[str] = deque([tid for tid, deg in in_degree.items() if deg == 0])
        sorted_tasks: list[Task] = []

        while queue:
            u = queue.popleft()
            sorted_tasks.append(self.tasks[u])
            for v in self._adj_out.get(u, set()):
                if v in in_degree:
                    in_degree[v] -= 1
                    if in_degree[v] == 0:
                        queue.append(v)

        if len(sorted_tasks) != len(self.tasks):
            raise TaskCycleError("Graph contains a cycle; topological sort not possible.")

        return sorted_tasks

    def evaluate_readiness(self, task_id: str) -> tuple[bool, list[BlockReason]]:
        """
        Deterministically evaluate if task_id is READY.
        A task is READY if:
        1. All BLOCKING active predecessor dependencies are satisfied (COMPLETED or APPROVED).
        2. No predecessor dependency has FAILED.
        """
        task = self.get_task(task_id)
        if task.status in {TaskStatus.COMPLETED, TaskStatus.APPROVED, TaskStatus.CANCELLED}:
            return False, []

        predecessors = self.get_predecessors(task_id)
        block_reasons: list[BlockReason] = []

        for pred in predecessors:
            if pred.status == TaskStatus.FAILED:
                block_reasons.append(BlockReason.DEPENDENCY_FAILED)
            elif pred.status not in {TaskStatus.COMPLETED, TaskStatus.APPROVED}:
                block_reasons.append(BlockReason.DEPENDENCY_INCOMPLETE)

        is_ready = len(block_reasons) == 0
        return is_ready, list(set(block_reasons))
