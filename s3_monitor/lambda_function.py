import gzip
import json
import base64
import logging
from datetime import datetime
import re
from typing import Any
import boto3

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def lambda_handler(event: Any, context: Any):
    """Hanlder to be called by AWS Lambda"""
    cw_client = boto3.client('cloudwatch', region_name='us-west-2')
    
    cw_data = event['awslogs']['data']
    compressed_payload = base64.b64decode(cw_data)
    uncompressed_payload = gzip.decompress(compressed_payload)
    payload = json.loads(uncompressed_payload)
    log_events = payload['logEvents']
    for log_event in log_events:
        message = json.loads(log_event['message'])
        if message['eventName'] == 'GetObject':
            nbyte = message['additionalEventData']['bytesTransferredOut']
            timestamp = datetime.fromisoformat(re.sub(r'Z$', '+00:00', message['eventTime']))
            logger.info(f'GetObject with {nbyte} bytes')
            cw_client.put_metric_data(
                MetricData=[
                    {
                        'MetricName': 'bytesTransferredOut',
                        'Dimensions': [],
                        'Unit': 'None',
                        'Value': nbyte,
                        'Timestamp': timestamp
                    }
                ],
                Namespace='XGBoostCICostWatcher'
            )
