import os
import logging

import boto3
import jenkinsapi
from requests.exceptions import HTTPError

# Seconds a Jenkins request might have until it times out
JENKINS_REQUEST_TIMEOUT_SECONDS = 300

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_jenkins_handle():
    jenkins_url = 'https://xgboost-ci.net'
    jenkins_username = os.environ.get('XGBOOST_DEVOPS_JENKINS_USERNAME')
    jenkins_token = os.environ.get('XGBOOST_DEVOPS_JENKINS_TOKEN')
    if not jenkins_username:
        error_msg = ('Jenkins username could not be located. ' +
                     'Set environment variable XGBOOST_DEVOPS_JENKINS_USERNAME')
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    if not jenkins_token:
        error_msg = ('Jenkins token could not be located. ' +
                     'Create an API token with your Jenkins account ' +
                     'and set environment variable XGBOOST_DEVOPS_JENKINS_TOKEN')
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    try:
        handle = jenkinsapi.jenkins.Jenkins(jenkins_url,
                                            username=jenkins_username,
                                            password=jenkins_token,
                                            timeout=JENKINS_REQUEST_TIMEOUT_SECONDS)
        logger.info('Successfully authenticated for Jenkins. Username: %s', jenkins_username)
    except HTTPError as e:
        error_msg = 'Error initializing Jenkins API.'
        logger.exception(error_msg)
        logger.error('HTML response:\n%s', e.response.content.decode('utf-8'))
        raise Exception(error_msg, e)
    return handle

def lambda_handler(event, context):
    handle = get_jenkins_handle()
    queue = handle.get_queue()
    keys = queue.keys()
    logger.info('Jenkins job queue: %s', keys)
    return {
        'statusCode': 200,
        'body': f'Jenkins job queue: {keys}'
    }
