from datetime import datetime, timedelta
from help_function.ETL_Data import *
from airflow import DAG 
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import pandas as pd
from datetime import datetime


dag = DAG(
    'ETL',
    description = " Pipeline",
    schedule_interval = '@hourly',
    start_date = datetime(2023, 10, 9),
)

data = ETL()
task1 = PythonOperator(
    task_id = 'get_config',
    python_callable = data.get_config,
    dag = dag
)

task2 = PythonOperator(
    task_id = 'crawl_data',
    python_callable = data.extract_data,
    op_args  = [task1.output],
    dag = dag
)

task3 = PythonOperator(
    task_id = 'transform_data',
    python_callable = data.transform_data,
    dag = dag
)
task4 = PythonOperator(
    task_id = 'load_data',
    python_callable = data.load,
    dag = dag
)

task1>>task2>>task3>>task4

