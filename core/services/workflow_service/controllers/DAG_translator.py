from airflow import DAG
from airflow.operators.postgres_operator import PostgresOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.mysql_operator import MySqlOperator
from airflow.utils.dates import days_ago
from datetime import timedelta


# translator from Project and Blocks to an Airflow DAG
def create_dag_from_project(project):
    # DAG based on project
    dag = DAG(
        dag_id=f"project_{project.uuid}",
        schedule_interval=project.schedule_interval,
        start_date=project.start_date,
        catchup=project.catchup,
        default_args={
            'retries': project.default_retries,
            'retry_delay': (
                timedelta(seconds=project.dag_timeout)
                if project.dag_timeout
                else timedelta(minutes=5)
            ),
        },
        concurrency=project.concurrency,
        dagrun_timeout=(
            timedelta(seconds=project.dag_timeout)
            if project.dag_timeout
            else None
        )
    )

    tasks = {}

    # tasks based on blocks
    for block in project.blocks:
        # Choose the right operator based on block_type
        if block.block_type == OperatorType.POSTGRES:
            tasks[block.uuid] = PostgresOperator(
                task_id=f"task_{block.uuid}",
                sql=block.parameters.get("sql"),
                postgres_conn_id=block.environment.get("db_conn_id", "default_postgres_conn"),
                dag=dag,
            )
        elif block.block_type == OperatorType.PYTHON:
            # Define a callable for the PythonOperator
            python_callable = load_callable(block.parameters.get("python_callable_path"))
            tasks[block.uuid] = PythonOperator(
                task_id=f"task_{block.uuid}",
                python_callable=python_callable,
                op_args=block.parameters.get("op_args", []),
                op_kwargs=block.parameters.get("op_kwargs", {}),
                dag=dag,
            )
        elif block.block_type == OperatorType.MYSQL:
            tasks[block.uuid] = MySqlOperator(
                task_id=f"task_{block.uuid}",
                sql=block.parameters.get("sql"),
                mysql_conn_id=block.environment.get("db_conn_id", "default_mysql_conn"),
                dag=dag,
            )

    # Set task dependencies based on block dependencies
    for block in project.blocks:
        for upstream_block in block.upstream_blocks:
            # >> is airflow-term for executing one before the other
            tasks[upstream_block.uuid] >> tasks[block.uuid] 

    return dag


def load_callable(python_callable_path):
    """
    Utility function to import a Python callable by path.
    Assumes format "module.submodule.function".
    """
    from importlib import import_module
    module_path, func_name = python_callable_path.rsplit(".", 1)
    module = import_module(module_path)
    return getattr(module, func_name)
