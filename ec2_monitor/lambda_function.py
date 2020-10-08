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

ec2_resource = boto3.resource('ec2', region_name='us-west-2')
table = boto3.resource('dynamodb', region_name='us-west-2').Table('XGBoostCIWorkerProvisionRecord')

def get_os_of_ami(image_id: str) -> str:
    image = ec2_resource.Image(image_id)
    platform_details = image.platform_details
    assert platform_details in ['Linux/UNIX', 'Windows']
    if platform_details == 'Linux/UNIX':
        return 'Linux'
    return platform_details

def lambda_handler(event: Any, context: Any):
    cw_data = event['awslogs']['data']
    compressed_payload = base64.b64decode(cw_data)
    uncompressed_payload = gzip.decompress(compressed_payload)
    payload = json.loads(uncompressed_payload)
    log_events = payload['logEvents']
    for log_event in log_events:
        message = json.loads(log_event['message'])
        if ('eventType' not in message):
            logger.debug(f'Message not well-formed: {message}')
            continue
        if message['eventType'] != 'AwsApiCall':
            # Skip events that are not API calls, such as Insights
            continue
        if ('eventName' not in message) or ('eventTime' not in message):
            logger.debug(f'Message not well-formed: {message}')
            continue
        event_name = message['eventName']
        event_time = message['eventTime']
        if event_name == 'RunInstances':
            if (('responseElements' not in message)
                    or (not message['responseElements'])
                    or ('instancesSet' not in message['responseElements'])
                    or (not message['responseElements']['instancesSet'])
                    or ('items' not in message['responseElements']['instancesSet'])):
                # RunInstance that did not succeed
                continue
            for ec2 in message['responseElements']['instancesSet']['items']:
                ec2_id = ec2['instanceId']
                ec2_type = ec2['instanceType']
                ec2_os = get_os_of_ami(ec2['imageId'])
                logger.info(f'RunInstances, InstanceID = {ec2_id} @ {event_time}')
                table.put_item(Item={
                    'Date': event_time.split(sep='T', maxsplit=1)[0],
                    'Timestamp': event_time,
                    'EventName': 'RunInstances',
                    'InstanceID': ec2_id,
                    'InstanceType': ec2_type,
                    'InstanceOS': ec2_os})
        elif event_name == 'TerminateInstances':
            if (('responseElements' not in message)
                    or (not message['responseElements'])
                    or ('instancesSet' not in message['responseElements'])
                    or (not message['responseElements']['instancesSet'])
                    or ('items' not in message['responseElements']['instancesSet'])):
                # TerminateInstances that did not succeed
                continue
            for ec2 in message['responseElements']['instancesSet']['items']:
                ec2_id = ec2['instanceId']
                logger.info(f'TerminateInstances, InstanceID = {ec2_id}  @ {event_time}')
                table.put_item(Item={
                    'Date': event_time.split(sep='T', maxsplit=1)[0],
                    'Timestamp': event_time,
                    'EventName': 'TerminateInstances',
                    'InstanceID': ec2_id})
