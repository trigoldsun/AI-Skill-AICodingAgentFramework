#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Manager - 任务管理器

任务规划和执行，灵感来源: claw-code/src/task.py
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any, Optional
from datetime import datetime
import logging


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """
    任务定义
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
    
    def __post_init__(self):
        if not self.id:
            self.id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    status: TaskStatus
    output: Any = None
    error: str = ""
    duration: float = 0.0


class TaskManager:
    """
    任务管理器
    
    管理任务的生命周期
    """
    
    def __init__(self):
        self.tasks: dict[str, Task] = {}
        self.logger = logging.getLogger(__name__)
    
    def create_task(
        self,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        **metadata
    ) -> Task:
        """
        创建任务
        
        Args:
            description: 任务描述
            priority: 优先级
            **metadata: 额外元数据
            
        Returns:
            Task: 创建的任务
        """
        task = Task(
            id=f"task_{len(self.tasks)}",
            description=description,
            priority=priority,
            metadata=metadata
        )
        self.tasks[task.id] = task
        self.logger.info(f"Created task: {task.id} - {description}")
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def update_status(self, task_id: str, status: TaskStatus) -> bool:
        """更新任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        task.status = status
        
        if status == TaskStatus.RUNNING:
            task.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.now()
        
        return True
    
    def add_step(self, task_id: str, step: dict) -> bool:
        """添加执行步骤"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        step["index"] = len(task.steps) + 1
        step["status"] = "pending"
        task.steps.append(step)
        return True
    
    def complete_task(
        self,
        task_id: str,
        result: Any = None,
        error: str = ""
    ) -> bool:
        """完成任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        task.result = result
        task.error = error
        task.status = TaskStatus.FAILED if error else TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        
        self.logger.info(f"Task {task.id} completed: {task.status.value}")
        return True
    
    def list_tasks(self, status: TaskStatus = None) -> list[Task]:
        """列出任务"""
        if status:
            return [t for t in self.tasks.values() if t.status == status]
        return list(self.tasks.values())
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        return self.update_status(task_id, TaskStatus.CANCELLED)
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self.tasks:
            self.tasks.pop(task_id)
            return True
        return False
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        stats = {
            "total": len(self.tasks),
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }
        
        for task in self.tasks.values():
            stats[task.status.value] = stats.get(task.status.value, 0) + 1
        
        return stats


class PipelineTaskManager(TaskManager):
    """
    管道任务管理器 - 支持任务编排
    """
    
    def create_pipeline(
        self,
        name: str,
        steps: list[dict]
    ) -> Task:
        """
        创建管道任务
        
        Args:
            name: 管道名称
            steps: 执行步骤列表
            
        Returns:
            Task: 管道任务
        """
        task = self.create_task(
            description=f"Pipeline: {name}",
            metadata={"type": "pipeline", "steps": steps}
        )
        task.steps = [
            {**step, "index": i, "status": "pending"}
            for i, step in enumerate(steps)
        ]
        return task
    
    def execute_pipeline(
        self,
        task_id: str,
        executors: dict[str, Callable]
    ) -> TaskResult:
        """
        执行管道任务
        
        Args:
            task_id: 任务ID
            executors: 步骤执行器映射
            
        Returns:
            TaskResult: 执行结果
        """
        task = self.get_task(task_id)
        if not task:
            return TaskResult(task_id, TaskStatus.FAILED, error="Task not found")
        
        self.update_status(task_id, TaskStatus.RUNNING)
        start_time = datetime.now()
        
        results = []
        for step in task.steps:
            step_name = step.get("name", "unknown")
            executor_name = step.get("executor", "echo")
            
            try:
                executor = executors.get(executor_name)
                if not executor:
                    raise ValueError(f"Executor not found: {executor_name}")
                
                result = executor(step.get("params", {}))
                results.append({"step": step_name, "result": result})
                step["status"] = "completed"
                
            except Exception as e:
                step["status"] = "failed"
                step["error"] = str(e)
                return self.complete_task(task_id, error=str(e))
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return TaskResult(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            output=results,
            duration=duration
        )
