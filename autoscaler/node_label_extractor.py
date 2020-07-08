import logging
import re
from typing import Set, Any, Optional, Dict, List

from worker_manager import find_worker_by_name
from metadata import recognized_jenkins_worker_labels

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Queue reasons being output by Jenkins.
RE_NO_AVAILABLE_WORKER = [
    r'(There are no nodes with the label ‘(?P<label>.*)’)',
    r'(All nodes of label ‘(?P<label>.*)’ are offline)',
    r'(doesn’t have label ‘(?P<label>.*)’)',
    r'(Waiting for next available executor on ‘(?P<label>.*)’)',
    r'(‘(?P<label>.*)’ is offline)',
]
RE_NO_AVAILABLE_WORKERS = r'(^Waiting for next available executor$)'

def label_from_queued_job(workers: List[Dict[str, Any]],
                          queued_job: Dict[str, Any]) -> Optional[Set[str]]:
    """
    Extract the worker type label from a queue item. The queue item contains a reason that states
    why it's currently hanging and exposes the name of the label it's waiting for. This label is
    extracted by this method.
    """
    # Check if there are no running workers in general. This is a special case since jenkins does
    # not tell which workers are actually required. In that case, just assume we need a Linux CPU
    # worker
    regex_result = re.search(RE_NO_AVAILABLE_WORKERS, queued_job['why'])
    if regex_result:
        logging.debug('There are no workers on the Jenkins master, creating Linux CPU worker to '
                      'start label propagation')
        label = {'linux', 'cpu'}
    else:
        for re_available_worker in RE_NO_AVAILABLE_WORKER:
            regex_result = re.search(re_available_worker, queued_job['why'])
            if regex_result:
                label = set([x.strip(' ‘’\'"') for x in regex_result.group('label').split('&&')])
                break
        else:
            return None
    logger.debug('label: %s', label)

    # Sometimes, Jenkins does not put the required label into the message but a worker-name instead.
    # In this case, we have to extract the label from the worker
    if not label.issubset(recognized_jenkins_worker_labels()):
        worker = None
        for name in label:
            worker = find_worker_by_name(workers=workers, name=name)
            if worker:
                logger.debug('Found worker with name "%s"', name)
                break
        if not worker:
            logging.error("Queue reason '%s' contains unresolvable label '%s'",
                          queued_job['why'], label)
            return None
        label = managed_worker_label(worker=worker)
        if not label:
            logging.error('Could not extract type label for worker %s as part of queue reason "%s"',
                          worker['displayName'], queued_job['why'])
            return None
    return label

def managed_worker_label(worker: Dict[str, Any]) -> Set[str]:
    """Extract the worker label e.g. linux && cpu or linux && gpu from a Jenkins worker."""
    display_name = worker['displayName']
    assigned_labels = set()
    # Convert list of tuples ('name' : 'label') to set
    for labels_dict in worker['assignedLabels']:
        assigned_labels.add(labels_dict['name'])
    return assigned_labels.intersection(recognized_jenkins_worker_labels())
