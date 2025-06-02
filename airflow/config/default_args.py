from datetime import timedelta

from src.utils import config


def get_dynamic_default_args():
    return {
        "owner": config.AIRFLOW_OWNER,
        "retries": config.AIRFLOW_RETRIES,
        "retry_delay": timedelta(minutes=config.AIRFLOW_RETRY_DELAY_MINUTES),
        "email": config.AIRFLOW_ALERT_EMAIL if config.AIRFLOW_ALERT_EMAIL else None,
        "email_on_failure": config.AIRFLOW_EMAIL_ON_FAILURE,
    }


# %%

KEY_LAST_FETCHING_DATE = "last_fetching_date"
KEY_FEATURE_DATASET_STORAGE_KEY = "feature_dataset_storage_key"
