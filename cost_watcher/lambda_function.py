import logging
import datetime
import json
import re
import math
from typing import Any, Dict, Tuple, Union

import boto3
from metadata import daily_budget

recognized_os_types = ['Linux', 'Windows']
recognized_instance_types = [
    'c5a.4xlarge', 'c5.4xlarge', 'g4dn.xlarge', 'g4dn.12xlarge', 'p2.xlarge', 'c5.large'
]

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def get_today_ec2_usage_record() -> Dict[str, Dict[str, Union[datetime.datetime, str]]]:
    ct_client = boto3.client('cloudtrail', region_name='us-west-2')
    ec2_client = boto3.client('ec2', region_name='us-west-2')

    today = datetime.datetime.now(datetime.timezone.utc)

    paginator = ct_client.get_paginator('lookup_events')
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
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
            for ec2 in event_detail['responseElements']['instancesSet']['items']:
                ec2_id = ec2['instanceId']
                if ec2_id not in ec2_run_record:
                    continue
                ec2_type = ec2['instanceType']
                r = ec2_client.describe_images(ImageIds=[ec2['imageId']])
                assert len(r['Images']) == 1
                ec2_os = r['Images'][0]['PlatformDetails']
                assert ec2_os in ['Linux/UNIX', 'Windows']
                if ec2_os == 'Linux/UNIX':
                    ec2_os = 'Linux'
                ec2_run_record[ec2_id]['start'] = event_time
                ec2_run_record[ec2_id]['type'] = ec2_type
                ec2_run_record[ec2_id]['os'] = ec2_os
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
    ec2_run_record = get_today_ec2_usage_record()
    cost_table = get_ec2_pricing()
    logger.debug('cost_table: %s', cost_table)
    today_cost = 0
    for ec2_id, record in ec2_run_record.items():
        assert 'end' in record
        if 'start' not in record:
            # There is up to 15 minute delay between API invocation and when CloudTrail records it
            # In a rare case, CloudTrail could have a record for terminating an instance but not
            # yet for starting it. Ignore this record for the purpose of estimating the daily cost.
            logger.info('CloudTrail has record for terminating instance %s (%s) but not for ' +
                        'starting it. Ignoring it for now.', ec2_id, record['end'].isoformat())
            continue
        duration = record['end'] - record['start']
        num_second = math.ceil(duration.total_seconds())
        if record['os'] == 'Linux':
            cost = max(num_second, 60) * cost_table[('Linux', record['type'])] / 3600
        else:
            assert record['os'] == 'Windows'
            num_hour = math.ceil(num_second / 3600)
            cost = num_hour * cost_table[('Windows', record['type'])]
        logger.debug('%s %s (%s), ran %d sec (%s~%s), cost %.2f USD', record['type'], record['os'],
                ec2_id, num_second, record['start'].isoformat(), record['end'].isoformat(), cost)
        today_cost += cost
    logger.info('Cost = %.2f USD', today_cost)
    threshold = daily_budget()

    cw_client = boto3.client('cloudwatch', region_name='us-west-2')
    cw_client.put_metric_data(
        MetricData=[
            {
                'MetricName': 'TodayEC2SpendingUSD',
                'Dimensions': [],
                'Unit': 'None',
                'Value': today_cost
            }
        ],
        Namespace='XGBoostCICostWatcher'
    )

    if today_cost > threshold:
        reason = (f"Today's spending ({today_cost:.2f} USD) exceeded the budget " +
                  f"({threshold:.2f} USD) allocated for today!")
        logger.info(reason)
        return {
            'approved' : False,
            'reason': reason
        }
    else:
        reason = (f"Today's spending ({today_cost:.2f} USD) is within the budget " +
                  f"({threshold:.2f} USD) allocated for today.")
        logger.info(reason)
        return {
            'approved' : True,
            'reason': reason
        }
