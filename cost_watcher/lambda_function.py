import logging
import datetime
import json
import re
import math
from typing import Any, Dict, Tuple, Union
import configparser

import boto3
from botocore.config import Config as BotoConfig

recognized_os_types = ['Linux', 'Windows']
recognized_instance_types = [
    'c5a.4xlarge', 'c5.4xlarge', 'g4dn.xlarge', 'g4dn.12xlarge', 'p2.xlarge', 'c5.large',
    't3a.large', 't3a.micro', 'g4dn.2xlarge'
]
no_launch_policy_arn = 'arn:aws:iam::492475357299:policy/EC2AccessNoRunInstances'

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ec2_resource = boto3.resource('ec2', region_name='us-west-2')
iam_resource = boto3.resource('iam', region_name='us-west-2')
ct_client = boto3.client('cloudtrail', region_name='us-west-2',
                         config = BotoConfig(retries={'max_attempts': 10, 'mode': 'standard'}))

config = configparser.ConfigParser()
config.read('./metadata.ini')

def turn_off_ec2_provision():
    """Prevent the Jenkins manager from launching new EC2 worker instances. This function is
    idempotent, i.e. it can be called multiple time without adverse effects."""
    policy = iam_resource.Policy(no_launch_policy_arn)
    policy.attach_role(RoleName='XGBoost-CI-Master')
    logger.info('Now the Jenkins manager cannot launch new EC2 worker instances')
    assert policy.attachment_count == 1

def turn_on_ec2_provision():
    """Allow the Jenkins manager to launch new EC2 worker instances. This function is idempotent,
    i.e. it can be called multiple times without adverse effects."""
    policy = iam_resource.Policy(no_launch_policy_arn)
    try:
        policy.detach_role(RoleName='XGBoost-CI-Master')
    except iam_resource.meta.client.exceptions.NoSuchEntityException as e:
        logger.debug('The Jenkins manager already can launch new EC2 instances')
    logger.info('Now the Jenkins manager can launch new EC2 worker instances')
    assert policy.attachment_count == 0

def get_os_of_ami(image_id: str) -> str:
    image = ec2_resource.Image(image_id)
    platform_details = image.platform_details
    assert platform_details in ['Linux/UNIX', 'Windows']
    if platform_details == 'Linux/UNIX':
        return 'Linux'
    return platform_details

def get_today_ec2_usage_record() -> Dict[str, Dict[str, Union[datetime.datetime, str]]]:
    current_time = datetime.datetime.now(datetime.timezone.utc)

    paginator = ct_client.get_paginator('lookup_events')
    today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + datetime.timedelta(days=1)

    ec2_run_record = {}

    page_iter = paginator.paginate(
        LookupAttributes=[
            {'AttributeKey': 'EventName', 'AttributeValue': 'TerminateInstances'}
        ],
        StartTime=today_start,
        EndTime=today_end
    )
    for page in page_iter:
        for event in page['Events']:
            assert event['EventName'] == 'TerminateInstances'
            event_time = event['EventTime']
            event_detail = json.loads(event['CloudTrailEvent'])
            for ec2 in event_detail['responseElements']['instancesSet']['items']:
                ec2_id = ec2['instanceId']
                ec2_run_record[ec2_id] = {'end': event_time}

    page_iter = paginator.paginate(
        LookupAttributes=[
            {'AttributeKey': 'EventName', 'AttributeValue': 'RunInstances'}
        ],
        StartTime=today_start - datetime.timedelta(days=1),
        EndTime=today_end
    )
    for page in page_iter:
        for event in page['Events']:
            assert event['EventName'] == 'RunInstances'
            event_time = event['EventTime']
            event_detail = json.loads(event['CloudTrailEvent'])
            if (('responseElements' not in event_detail)
                    or (not event_detail['responseElements'])
                    or ('instancesSet' not in event_detail['responseElements'])
                    or (not event_detail['responseElements']['instancesSet'])):
                # RunInstance that did not succeed
                continue
            for ec2 in event_detail['responseElements']['instancesSet']['items']:
                ec2_id = ec2['instanceId']
                if ec2_id not in ec2_run_record:
                    # This instance is currently active; will count it in get_active_ec2_instances()
                    continue
                ec2_run_record[ec2_id]['start'] = event_time
                ec2_run_record[ec2_id]['type'] = ec2['instanceType']
                ec2_run_record[ec2_id]['os'] = get_os_of_ami(ec2['imageId'])
    return ec2_run_record

def get_active_ec2_instances() -> Dict[str, Dict[str, Union[datetime.datetime, str]]]:
    ec2 = boto3.resource('ec2', region_name='us-west-2')
    ec2_iter = ec2.instances.filter(
        Filters=[
            {'Name': 'instance-state-name',
             'Values': ['pending', 'running', 'shutting-down', 'stopping']}
        ]
    )
    current_time = datetime.datetime.now(datetime.timezone.utc)
    today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

    ec2_run_record = {}

    for instance in ec2_iter:
        launch_time = instance.launch_time.astimezone(tz=datetime.timezone.utc)
        duration = current_time - launch_time
        tags = {x['Key'] : x['Value'] for x in instance.tags}
        # Exclude the Jenkins manager instance
        if 'Name' in tags and tags['Name'] in ['Jenkins manager', 'Jenkins Job Initializer']:
            continue
        ec2_run_record[instance.instance_id] = {
            'start': launch_time,
            'end': current_time,
            'type': instance.instance_type,
            'os': get_os_of_ami(instance.image_id)
        }
    return ec2_run_record

def get_ec2_pricing() -> Dict[Tuple[str, str], float]:
    client = boto3.client('pricing', region_name='us-east-1')

    region_name = 'US West (Oregon)'
    cost_table = {}

    for instance_type in recognized_instance_types:
        r = client.get_products(
            ServiceCode='AmazonEC2',
            Filters=[
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region_name},
                {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'},
                {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type}
            ],
            FormatVersion='aws_v1'
        )
        for e in r['PriceList']:
            obj = json.loads(e)
            product_record = obj['product']
            if product_record['productFamily'] != 'Compute Instance':
                continue
            product_attrs = product_record['attributes']
            os_type = product_attrs['operatingSystem']
            if os_type not in recognized_os_types:
                continue
            instance_type_ = product_attrs['instanceType']
            assert instance_type_ == instance_type
            assert product_attrs['location'] == region_name
            assert product_attrs['tenancy'] == 'Shared'
            assert product_attrs['capacitystatus'] == 'Used'
            assert product_attrs['preInstalledSw'] == 'NA'
            assert re.match(r'^RunInstances(?::[0-9g]{4}){0,1}$', product_attrs['operation'])
            price_record = obj['terms']['OnDemand']
            id1 = list(price_record)[0]
            id2 = list(price_record[id1]['priceDimensions'])[0]
            price_record = price_record[id1]['priceDimensions'][id2]
            assert 'USD' in price_record['pricePerUnit']
            assert price_record['unit'] == 'Hrs'
            cost_table[(os_type, instance_type)] = float(price_record['pricePerUnit']['USD'])
    return cost_table

def lambda_handler(event: Any, context: Any):
    """Hanlder to be called by AWS Lambda"""
    cost_table = get_ec2_pricing()
    logger.debug('cost_table: %s', cost_table)
    today_cost = 0

    def estimate_cost(record: Dict[str, Union[datetime.datetime, str]]) -> float:
        duration = record['end'] - record['start']
        num_second = math.ceil(duration.total_seconds())
        if record['os'] == 'Linux':
            # Linux instances use per-second billing, with a minimum commitment of 60 seconds
            return max(num_second, 60) * cost_table[('Linux', record['type'])] / 3600
        assert record['os'] == 'Windows'
        # Windows instances use per-hour billing, with the usage time rounded up to the next hour.
        num_hour = math.ceil(num_second / 3600)
        return num_hour * cost_table[('Windows', record['type'])]

    for ec2_id, record in get_today_ec2_usage_record().items():
        assert 'end' in record
        if 'start' not in record:
            # There is up to 15 minute delay between API invocation and when CloudTrail records it
            # In a rare case, CloudTrail could have a record for terminating an instance but not
            # yet for starting it. Ignore this record for the purpose of estimating the daily cost.
            logger.info('CloudTrail has record for terminating instance %s (%s) but not for ' +
                        'starting it. Ignoring it for now.', ec2_id, record['end'].isoformat())
            continue
        duration = record['end'] - record['start']
        cost = estimate_cost(record)
        logger.debug('%s %s (%s), ran %d sec (%s~%s), cost %.2f USD', record['type'], record['os'],
                ec2_id, duration.total_seconds(), record['start'].isoformat(),
                record['end'].isoformat(), cost)
        today_cost += cost

    for ec2_id, record in get_active_ec2_instances().items():
        duration = record['end'] - record['start']
        cost = estimate_cost(record)
        logger.debug('%s %s (%s), ran %d sec (%s~Now), cost %.2f USD', record['type'], record['os'],
                ec2_id, duration.total_seconds(), record['start'].isoformat(), cost)
        today_cost += cost

    logger.info('Cost = %.2f USD', today_cost)
    daily_budget = float(config['DEFAULT']['daily_budget'])

    cw_client = boto3.client('cloudwatch', region_name='us-west-2')
    cw_client.put_metric_data(
        MetricData=[
            {
                'MetricName': 'TodayEC2SpendingUSD',
                'Dimensions': [],
                'Unit': 'None',
                'Value': today_cost
            },
            {
                'MetricName': 'DailyBudgetUSD',
                'Dimensions': [],
                'Unit': 'None',
                'Value': daily_budget
            }
        ],
        Namespace='XGBoostCICostWatcher'
    )

    if today_cost > daily_budget:
        reason = (f"Today's spending ({today_cost:.2f} USD) exceeded the budget " +
                  f"({daily_budget:.2f} USD) allocated for today! The spending limit gets reset " +
                  f"every midnight UTC. You can monitor the spending at the dashboard " +
                  "https://xgboost-ci.net/dashboard/.")
        logger.info(reason)
        turn_off_ec2_provision()
        return {
            'approved' : False,
            'reason': reason
        }
    else:
        reason = (f"Today's spending ({today_cost:.2f} USD) is within the budget " +
                  f"({daily_budget:.2f} USD) allocated for today.")
        logger.info(reason)
        turn_on_ec2_provision()
        return {
            'approved' : True,
            'reason': reason
        }
