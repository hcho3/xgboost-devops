import logging
from typing import Any, Dict, Union

from jenkins_connector import jenkins_handle
from node_label_extractor import label_from_queued_job, managed_worker_label

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def lambda_handler(event: Any, context: Any) -> Dict[str, Union[int, str]]:
    handle = jenkins_handle()
    queue_items = handle.get_queue()._data['items']
    workers = handle.get_nodes()._data['computer']
    job_labels = [label_from_queued_job(workers=workers, queued_job=x) for x in queue_items]
    worker_labels = [managed_worker_label(x) for x in workers]
    logger.info('Queued jobs\' label: %s', job_labels)
    logger.info('Jenkins workers: %s', worker_labels)
    return {
        'statusCode': 200,
        'body': {
            'Queued jobs label': [(list(x) if x else None) for x in job_labels],
            'Jenkins workers label': [(list(x) if x else None) for x in worker_labels]
        }
    }
