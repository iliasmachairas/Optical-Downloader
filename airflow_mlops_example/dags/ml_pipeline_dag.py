"""
Basic MLOps pipeline DAG using Apache Airflow.

Pipeline stages: data ingestion -> preprocessing -> training -> evaluation -> (optional) deployment
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from data_ingestion import ingest_data
from preprocessing import preprocess_data
from training import train_model
from evaluation import evaluate_model

DEFAULT_ARGS = {
    "owner": "mlops-team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="ml_training_pipeline",
    default_args=DEFAULT_ARGS,
    description="End-to-end ML training pipeline",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["mlops", "training"],
) as dag:

    ingest_task = PythonOperator(
        task_id="ingest_data",
        python_callable=ingest_data,
        op_kwargs={"output_path": "/tmp/raw_data.csv"},
    )

    preprocess_task = PythonOperator(
        task_id="preprocess_data",
        python_callable=preprocess_data,
        op_kwargs={
            "input_path": "/tmp/raw_data.csv",
            "output_path": "/tmp/processed_data.csv",
        },
    )

    train_task = PythonOperator(
        task_id="train_model",
        python_callable=train_model,
        op_kwargs={
            "data_path": "/tmp/processed_data.csv",
            "model_path": "/tmp/model.pkl",
        },
    )

    evaluate_task = PythonOperator(
        task_id="evaluate_model",
        python_callable=evaluate_model,
        op_kwargs={
            "data_path": "/tmp/processed_data.csv",
            "model_path": "/tmp/model.pkl",
            "metrics_path": "/tmp/metrics.json",
        },
    )

    ingest_task >> preprocess_task >> train_task >> evaluate_task
