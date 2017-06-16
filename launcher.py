import json

from store_results import store_results
from profilers.utils import get_sandbox
from profilers.posix_core import PosixCoreProfiler

## Entrace point - handlers for different environments

def lambda_handler(event, context):
    env = get_sandbox()
    
    ## in the future, can do something like
    ## if env == 'foo', run this profiler
    results = PosixCoreProfiler.run()

    results['sandbox'] = env

    if store_results(results) is None:
        print(json.dumps(results))

    return results

def wrapper():
    """Helper for easily calling this from a command line locally.

    Example: `python -c 'import main; main.wrapper()' | jq '.'`
    """
    res = lambda_handler(None, None)
    return res

