from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import TaskResult


def add_result(
    session: Session,
    task_name: str,
    value: float,
) -> TaskResult:
    result = TaskResult(
        task_name=task_name,
        value=value,
    )

    session.add(result)

    return result


def get_results(
    session: Session,
    limit: int = 100,
) -> list[TaskResult]:
    statement = (
        select(TaskResult)
        .order_by(TaskResult.id.desc())
        .limit(limit)
    )

    return list(session.scalars(statement).all())