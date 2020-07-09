import logging
from datetime import datetime
from typing import Any, Dict

import boto3
from jenkins_connector import jenkins_handle

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def get_this_month_ec2_spend() -> Dict[str, str]:
    """Query the money (cost) spent on EC2 this month so far"""
    client = boto3.client('ce', region_name='us-west-2')
    today = datetime.today()
    date_start = today.replace(day=1).strftime('%Y-%m-%d')
    date_end = today.replace(month=today.month + 1, day=1).strftime('%Y-%m-%d')
    logger.debug('Date queried: [%s, %s)', date_start, date_end)
    r = client.get_cost_and_usage(
        TimePeriod={'Start': date_start, 'End': date_end},
        Granularity='MONTHLY',
        Filter={'And': [
            {'Dimensions': {'Key': 'RECORD_TYPE', 'Values': ['Usage']}},
            {'Dimensions': {'Key': 'SERVICE', 'Values': ['Amazon Elastic Compute Cloud - Compute']}}
        ]},
        Metrics=['AmortizedCost']
    )
    cost = r['ResultsByTime'][0]['Total']['AmortizedCost']
    cost['Amount'] = float(cost['Amount'])
    return cost

def lambda_handler(event: Any, context: Any):
    """Hanlder to be called by AWS Lambda"""
    handle = jenkins_handle()
    logger.info('Jenkins version: %s', handle.version)
    cost = get_this_month_ec2_spend()
    logger.info('This month, we spent %.2f %s on EC2 so far.', cost['Amount'], cost['Unit'])
