import os
from datetime import datetime,timedelta

warm_file = "/tmp/lambda-is-warm"

def is_warm():
    """Returns true/false whether the lambda function is warm,
    as determined by whether or not warm_file exists.
    """
    return os.path.isfile(warm_file)

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, None)

def mark_warm():
    """Mark the lambda function as warm.
    """
    if not is_warm():
        with open(warm_file, 'a'):
            os.utime(warm_file, None)

def warm_since():
    """Return the date when the current warm version of the fn started.
    """
    if is_warm():
        ts = os.path.getmtime(warm_file)
        return datetime.fromtimestamp(ts)

def warm_for():
    """Return the elapsed time that the fn has been warm for."""
    if is_warm():
        ts = os.path.getmtime(warm_file)
        warm_start = datetime.fromtimestamp(ts)
        now = datetime.now()
        return now - warm_start
    else:
        return timedelta(0)
    
