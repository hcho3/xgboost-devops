from typing import Set

def recognized_jenkins_worker_labels() -> Set[str]:
    return {'linux', 'win64', 'build', 'cuda9', 'cuda10', 'cuda10_0', 'cuda10_1', 'cuda10_2',
            'cpu', 'cpu_build', 'gpu', 'mgpu', 'master'}
