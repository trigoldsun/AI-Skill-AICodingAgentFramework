"""
Task Manager - Task lifecycle management with TaskRegistry

Inspired by claw-code's TaskRegistry:
- In-memory task lifecycle management
- Thread-safe task operations
- State transitions with timestamps
- Task output and progress tracking

Task Lifecycle:
    PENDING -> RUNNING -> COMPLETED
                 ↓
              FAILED / CANCELLED
"""

from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class TaskStatus(Enum):
    """Task lifecycle states"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """
    Task definition with full lifecycle tracking.

    Attributes:
        id: Unique task identifier
        description: Human-readable task description
        status: Current lifecycle state
        priority: Task priority
        created_at: Creation timestamp
        started_at: When task started execution
        completed_at: When task completed
        steps: List of execution steps
        result: Task execution result
        error: Error message if failed
        metadata: Additional task metadata
        tags: Task categorization tags
        assignee: Agent assigned to this task
    """
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    steps: list[dict] = field(default_factory=list)
    result: Any = None
    error: str = ""
    metadata: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    assignee: str = ""

    def __post_init__(self):
        """Generate ID if not provided"""
        if not self.id:
            self.id = f"task_{uuid.uuid4().hex[:12]}"

    def duration(self) -> Optional[float]:
        """Calculate task duration in seconds"""
        if self.started_at:
            end = self.completed_at or datetime.now()
            return (end - self.started_at).total_seconds()
        return None


@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    status: TaskStatus
    output: Any = None
    error: str = ""
    duration: float = 0.0


class TaskRegistry:
    """
    Thread-safe in-memory task registry.

    Inspired by claw-code's TaskRegistry:
    - create(): Create new task with ID
    - get(): Retrieve task by ID
    - list(): List tasks with optional status filter
    - stop(): Cancel running task
    - update(): Update task state
    - output(): Append to task output
    - set_status(): Atomic status transition

    All operations are thread-safe via a lock.
    """

    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger("task_registry")

        # Event callbacks
        self._on_status_change: List[Callable[[Task, TaskStatus], None]] = []
        self._on_complete: List[Callable[[Task], None]] = []
        self._on_fail: List[Callable[[Task], None]] = []

    def create(
        self,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        tags: List[str] = None,
        assignee: str = None,
        **metadata
    ) -> Task:
        """
        Create a new task.

        Args:
            description: Human-readable task description
            priority: Task priority level
            tags: Optional categorization tags
            assignee: Agent ID assigned to this task
            **metadata: Additional metadata

        Returns:
            Created Task instance
        """
        with self._lock:
            task = Task(
                id=f"task_{uuid.uuid4().hex[:12]}",
                description=description,
                priority=priority,
                tags=tags or [],
                assignee=assignee or "",
                metadata=metadata
            )
            self._tasks[task.id] = task
            self._logger.info(f"Created task: {task.id} - {description}")
            return task

    def get(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        with self._lock:
            return self._tasks.get(task_id)

    def list(
        self,
        status: TaskStatus = None,
        tags: List[str] = None,
        assignee: str = None
    ) -> List[Task]:
        """
        List tasks with optional filters.

        Args:
            status: Filter by status
            tags: Filter by tags (task must have all specified tags)
            assignee: Filter by assignee

        Returns:
            List of matching tasks
        """
        with self._lock:
            tasks = list(self._tasks.values())

            if status:
                tasks = [t for t in tasks if t.status == status]

            if tags:
                tasks = [t for t in tasks if all(tag in t.tags for tag in tags)]

            if assignee:
                tasks = [t for t in tasks if t.assignee == assignee]

            # Sort by priority then creation time
            tasks.sort(key=lambda t: (-t.priority.value, t.created_at))

            return tasks

    def stop(self, task_id: str) -> bool:
        """
        Stop a running task.

        Args:
            task_id: Task to stop

        Returns:
            True if task was stopped
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                self._logger.info(f"Stopped task: {task_id}")
                return True

            return False

    def update(
        self,
        task_id: str,
        description: str = None,
        priority: TaskPriority = None,
        tags: List[str] = None,
        assignee: str = None
    ) -> bool:
        """
        Update task properties.

        Args:
            task_id: Task to update
            description: New description
            priority: New priority
            tags: New tags (replaces existing)
            assignee: New assignee

        Returns:
            True if task was updated
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            if description:
                task.description = description
            if priority:
                task.priority = priority
            if tags is not None:
                task.tags = tags
            if assignee is not None:
                task.assignee = assignee

            return True

    def set_status(
        self,
        task_id: str,
        status: TaskStatus,
        error: str = None,
        result: Any = None
    ) -> bool:
        """
        Atomically update task status.

        This is the primary method for status transitions.
        It handles the state machine logic and emits events.

        Args:
            task_id: Task to update
            status: New status
            error: Error message (for FAILED status)
            result: Task result (for COMPLETED status)

        Returns:
            True if status was updated
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            old_status = task.status
            task.status = status

            # Update timestamps based on transition
            if status == TaskStatus.RUNNING and not task.started_at:
                task.started_at = datetime.now()

            elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                task.completed_at = datetime.now()

            if error is not None:
                task.error = error

            if result is not None:
                task.result = result

            # Emit events
            self._emit_status_change(task, old_status)

            self._logger.debug(f"Task {task_id}: {old_status.value} -> {status.value}")
            return True

    def add_step(
        self,
        task_id: str,
        step: dict
    ) -> bool:
        """
        Add an execution step to a task.

        Args:
            task_id: Task to update
            step: Step definition with name, status, etc.

        Returns:
            True if step was added
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            step["index"] = len(task.steps) + 1
            if "status" not in step:
                step["status"] = "pending"

            task.steps.append(step)
            return True

    def update_step(
        self,
        task_id: str,
        step_index: int,
        status: str = None,
        result: Any = None,
        error: str = None
    ) -> bool:
        """
        Update a specific step.

        Args:
            task_id: Task ID
            step_index: Step index (1-based)
            status: New status
            result: Step result
            error: Step error

        Returns:
            True if step was updated
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or step_index > len(task.steps):
                return False

            step = task.steps[step_index - 1]
            if status:
                step["status"] = status
            if result is not None:
                step["result"] = result
            if error:
                step["error"] = error

            return True

    def append_output(
        self,
        task_id: str,
        output: str
    ) -> bool:
        """
        Append to task output stream.

        Args:
            task_id: Task ID
            output: Output text to append

        Returns:
            True if output was appended
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            if task.result is None:
                task.result = ""

            task.result = str(task.result) + output
            return True

    def get_stats(self) -> dict:
        """
        Get task statistics.

        Returns:
            Dict with counts by status
        """
        with self._lock:
            stats = {
                "total": len(self._tasks),
                "pending": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
                "timeout": 0,
            }

            for task in self._tasks.values():
                stats[task.status.value] = stats.get(task.status.value, 0) + 1

            return stats

    def on_status_change(
        self,
        callback: Callable[[Task, TaskStatus], None]
    ) -> None:
        """Register callback for status changes"""
        self._on_status_change.append(callback)

    def on_complete(self, callback: Callable[[Task], None]) -> None:
        """Register callback for task completion"""
        self._on_complete.append(callback)

    def on_fail(self, callback: Callable[[Task], None]) -> None:
        """Register callback for task failure"""
        self._on_fail.append(callback)

    def _emit_status_change(self, task: Task, old_status: TaskStatus) -> None:
        """Emit internal events for status change"""
        # Notify status change listeners
        for callback in self._on_status_change:
            try:
                callback(task, old_status)
            except Exception as e:
                self._logger.error(f"Status change callback failed: {e}")

        # Notify completion listeners
        if task.status == TaskStatus.COMPLETED:
            for callback in self._on_complete:
                try:
                    callback(task)
                except Exception as e:
                    self._logger.error(f"Complete callback failed: {e}")

        # Notify failure listeners
        elif task.status == TaskStatus.FAILED:
            for callback in self._on_fail:
                try:
                    callback(task)
                except Exception as e:
                    self._logger.error(f"Fail callback failed: {e}")


class TaskManager:
    """
    High-level task management API.

    This is a wrapper around TaskRegistry that provides:
    - Convenience methods for common operations
    - Pipeline/task chain support
    - Batch operations
    """

    def __init__(self):
        self.registry = TaskRegistry()

    def create_task(
        self,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        **metadata
    ) -> Task:
        """Create a new task"""
        return self.registry.create(description, priority, **metadata)

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self.registry.get(task_id)

    def list_tasks(self, status: TaskStatus = None) -> List[Task]:
        """List tasks with optional status filter"""
        return self.registry.list(status=status)

    def start_task(self, task_id: str) -> bool:
        """Start a pending task"""
        return self.registry.set_status(task_id, TaskStatus.RUNNING)

    def complete_task(
        self,
        task_id: str,
        result: Any = None
    ) -> bool:
        """Mark task as completed"""
        return self.registry.set_status(task_id, TaskStatus.COMPLETED, result=result)

    def fail_task(self, task_id: str, error: str) -> bool:
        """Mark task as failed"""
        return self.registry.set_status(task_id, TaskStatus.FAILED, error=error)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        return self.registry.stop(task_id)

    def add_step(self, task_id: str, step: dict) -> bool:
        """Add step to task"""
        return self.registry.add_step(task_id, step)

    def get_stats(self) -> dict:
        """Get task statistics"""
        return self.registry.get_stats()


class PipelineTaskManager(TaskManager):
    """
    Task manager with pipeline support.

    Enables creating multi-step pipelines where each step
    depends on the previous step's output.
    """

    def create_pipeline(
        self,
        name: str,
        steps: List[dict]
    ) -> Task:
        """
        Create a pipeline task.

        Args:
            name: Pipeline name
            steps: List of step definitions

        Returns:
            Task with pipeline metadata
        """
        task = self.create_task(
            description=f"Pipeline: {name}",
            tags=["pipeline"],
            metadata={"type": "pipeline", "steps": steps}
        )

        # Initialize steps
        for i, step in enumerate(steps):
            self.add_step(task.id, {
                "name": step.get("name", f"step_{i}"),
                "executor": step.get("executor", "echo"),
                "params": step.get("params", {}),
                "status": "pending"
            })

        return task

    async def execute_pipeline(
        self,
        task_id: str,
        executors: Dict[str, Callable]
    ) -> TaskResult:
        """
        Execute a pipeline task.

        Args:
            task_id: Pipeline task ID
            executors: Map of executor name to callable

        Returns:
            TaskResult with all step outputs
        """
        task = self.get_task(task_id)
        if not task:
            return TaskResult(task_id, TaskStatus.FAILED, error="Task not found")

        self.start_task(task_id)
        results = []

        for i, step in enumerate(task.steps):
            step_name = step.get("name", f"step_{i}")
            executor_name = step.get("executor", "echo")

            try:
                executor = executors.get(executor_name)
                if not executor:
                    raise ValueError(f"Executor not found: {executor_name}")

                result = await executor(step.get("params", {}))
                results.append({"step": step_name, "result": result})
                self.registry.update_step(task_id, i + 1, status="completed", result=result)

            except Exception as e:
                self.registry.update_step(task_id, i + 1, status="failed", error=str(e))
                self.fail_task(task_id, str(e))
                return TaskResult(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    error=str(e),
                    duration=task.duration() or 0.0
                )

        self.complete_task(task_id, result=results)
        return TaskResult(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            output=results,
            duration=task.duration() or 0.0
        )
