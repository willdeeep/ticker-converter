"""Helper functions for Airflow integration tests.
        # Create new DagRun
        from airflow.utils.types import DagRunType
        from airflow.utils.timezone import utcnow
        
        dag_run = DagRun(
            dag_id=dag.dag_id,
            run_id=run_id,
            logical_date=logical_date,
            start_date=utcnow(),
            state="running",
            run_type=DagRunType.MANUAL,
        ) provides utilities for creating and managing Airflow test instances
that are compatible with Airflow 3.x. The functions handle proper DagRun and 
TaskInstance creation to avoid database constraint violations.
"""

import signal
import time
from typing import Optional, Any, Callable
from uuid import uuid4

def create_test_dagrun_with_db_session(dag, logical_date=None):
    """Create a test DagRun with proper database session handling.
    
    This function creates a DagRun that will be persisted to the database,
    which is required for TaskInstance creation in Airflow 3.x.
    
    Args:
        dag: The DAG to create a run for
        logical_date: Optional logical date for the run
        
    Returns:
        str: The run_id of the created DagRun
    """
    from airflow.models import DagRun
    from airflow import settings
    from sqlalchemy.orm import sessionmaker
    
    if logical_date is None:
        from airflow.utils.timezone import utcnow
        logical_date = utcnow()
    
    # Generate unique run_id
    from airflow.utils.timezone import utcnow
    run_id = f"test_run_{utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
    
    Session = sessionmaker(bind=settings.engine)
    session = Session()
    
    try:
        # Check if DagRun already exists
        existing = session.query(DagRun).filter(
            DagRun.dag_id == dag.dag_id,
            DagRun.run_id == run_id
        ).first()
        
        if existing:
            session.close()
            return existing.run_id
        
        # Create new DagRun
        from airflow.utils.types import DagRunType
        from airflow.utils.timezone import utcnow
        
        dag_run = DagRun(
            dag_id=dag.dag_id,
            run_id=run_id,
            logical_date=logical_date,
            start_date=utcnow(),
            state="running",
            run_type=DagRunType.MANUAL,
        )
        
        session.add(dag_run)
        session.commit()
        session.close()
        
        return run_id
        
    except Exception as e:
        session.rollback()
        session.close()
        raise e


def create_test_task_instance(task, logical_date=None):
    """Create a TaskInstance for testing with proper DagRun persistence.
    
    This function creates a TaskInstance that's properly linked to a persisted
    DagRun, which prevents UNIQUE constraint violations in Airflow 3.x.
    
    Args:
        task: The task to create an instance for
        logical_date: Optional logical date for the task instance
        
    Returns:
        TaskInstance: Ready to run task instance
    """
    from airflow.models import TaskInstance
    
    run_id = create_test_dagrun_with_db_session(task.dag, logical_date)
    return TaskInstance(task=task, run_id=run_id)


def run_task_with_timeout(task_instance, timeout_seconds=30):
    """Run a TaskInstance with timeout handling for Airflow 3.x.
    
    This function runs a task in the main thread with proper timeout handling,
    avoiding the signal handling issues that occur when running tasks in threads.
    
    Args:
        task_instance: The TaskInstance to run
        timeout_seconds: Maximum time to allow for task execution
        
    Returns:
        Any: Task result or None if timeout/error
        
    Raises:
        TimeoutError: If task execution exceeds timeout
        Exception: Re-raises any exception from task execution
    """
    class TimeoutException(Exception):
        pass
    
    def timeout_handler(signum, frame):
        raise TimeoutException(f"Task execution timed out after {timeout_seconds} seconds")
    
    # Set up timeout signal handler (only works in main thread)
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        result = task_instance.run()
        signal.alarm(0)  # Cancel the alarm
        return result
    except TimeoutException:
        raise TimeoutError(f"Task execution timed out after {timeout_seconds} seconds")
    except Exception as e:
        signal.alarm(0)  # Cancel the alarm
        raise e
    finally:
        # Restore original signal handler
        signal.signal(signal.SIGALRM, old_handler)


def clean_test_dagruns(dag_id_pattern="test_"):
    """Clean up test DagRuns from database.
    
    Args:
        dag_id_pattern: Pattern to match DAG IDs for cleanup
    """
    from airflow.models import DagRun
    from airflow import settings
    from sqlalchemy.orm import sessionmaker
    
    Session = sessionmaker(bind=settings.engine)
    session = Session()
    
    try:
        # Delete test DagRuns
        deleted = session.query(DagRun).filter(
            DagRun.dag_id.like(f"%{dag_id_pattern}%")
        ).delete(synchronize_session=False)
        
        session.commit()
        session.close()
        
        return deleted
        
    except Exception as e:
        session.rollback()
        session.close()
        raise e
