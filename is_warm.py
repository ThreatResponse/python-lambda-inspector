import os
from datetime import datetime,timedelta

warm_file = "/tmp/lambda-is-warm"

def is_warm():
    """Returns warm/not warm/not possible
       to denote if the aws lambda function is warm,
       as determined by whether or not warm_file exists (warm/not warm)
       or if the filesystem is readonly (not possible)
    """
    if os.access(os.path.dirname(warm_file),os.W_OK):
        if os.path.isfile(warm_file):
            return 'warm'
        else:
            return 'not warm'
    else:
        return 'not possible'

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, None)

def mark_warm():
    """Mark the lambda function as warm.
    """
    if is_warm() == 'not warm':
        try:
            with open(warm_file, 'a'):
                os.utime(warm_file, None)
        except IOError as e:
            pass

def warm_since():
    """Return the date when the current warm version of the fn started.
    """
    if is_warm() == 'warm':
        ts = os.path.getmtime(warm_file)
        return ts

def warm_for():
    """Return the elapsed time that the fn has been warm for."""
    if is_warm() == 'warm':
        ts = os.path.getmtime(warm_file)
        warm_start = datetime.fromtimestamp(ts)
        now = datetime.now()
        return (now - warm_start).total_seconds()
    else:
        return timedelta(0)
