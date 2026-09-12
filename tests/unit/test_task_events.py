"""
Unit tests for Phase 4 Task Engine Domain Events.
"""

from src.domain.events import (
    TaskApprovedEvent,
    TaskBlockedEvent,
    TaskCancelledEvent,
    TaskCompletedEvent,
    TaskCreatedEvent,
    TaskDependencyAddedEvent,
    TaskDependencyRemovedEvent,
    TaskExecutionFailedEvent,
    TaskExecutionStartedEvent,
    TaskFailedEvent,
    TaskReadyEvent,
    TaskRetryScheduledEvent,
    TaskReviewRequestedEvent,
    TaskReworkRequestedEvent,
    TaskStatusChangedEvent,
)


def test_task_events_instantiation() -> None:
    e1 = TaskCreatedEvent(task_id="t1", plan_id="p1", title="Task 1")
    assert e1.task_id == "t1"
    assert e1.plan_id == "p1"

    e2 = TaskStatusChangedEvent(task_id="t1", previous_status="CREATED", new_status="PLANNED")
    assert e2.previous_status == "CREATED"

    e3 = TaskDependencyAddedEvent(
        dependency_id="dep1", predecessor_task_id="t1", successor_task_id="t2"
    )
    assert e3.predecessor_task_id == "t1"

    e4 = TaskDependencyRemovedEvent(
        dependency_id="dep1", predecessor_task_id="t1", successor_task_id="t2"
    )
    assert e4.dependency_id == "dep1"

    e5 = TaskBlockedEvent(task_id="t2", block_reasons=["DEPENDENCY_INCOMPLETE"])
    assert "DEPENDENCY_INCOMPLETE" in e5.block_reasons

    e6 = TaskReadyEvent(task_id="t2")
    assert e6.task_id == "t2"

    e7 = TaskExecutionStartedEvent(task_id="t1", employee_id="emp1", execution_run_id="run1")
    assert e7.execution_run_id == "run1"

    e8 = TaskExecutionFailedEvent(task_id="t1", execution_run_id="run1", error="Timeout")
    assert e8.error == "Timeout"

    e9 = TaskReviewRequestedEvent(task_id="t1", execution_run_id="run1")
    assert e9.task_id == "t1"

    e10 = TaskReworkRequestedEvent(task_id="t1", reason="Format error")
    assert e10.reason == "Format error"

    e11 = TaskApprovedEvent(task_id="t1", approved_by="mgr1")
    assert e11.approved_by == "mgr1"

    e12 = TaskCompletedEvent(task_id="t1")
    assert e12.task_id == "t1"

    e13 = TaskFailedEvent(task_id="t1", reason="Failed")
    assert e13.task_id == "t1"

    e14 = TaskCancelledEvent(task_id="t1", reason="Cancelled")
    assert e14.reason == "Cancelled"

    e15 = TaskRetryScheduledEvent(task_id="t1", retry_count=1, max_retries=3)
    assert e15.retry_count == 1
