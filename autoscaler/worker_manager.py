import logging
from typing import Optional, List, Dict, Any

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def find_worker_by_name(workers: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    """Loop through a list of workers and return the one which has the matching display name"""
    # Workers always have unique names, thus there's no need for duplicate check
    for worker in workers:
        if name == worker['displayName']:
            return worker
    return None
