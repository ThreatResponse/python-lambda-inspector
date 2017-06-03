import os
from datetime import datetime, timedelta


def warm_file():
    """
    Determine what the OS is and change the warm location accordingly.
    """
    if os.getenv('AWS_ACCESS_KEY_ID', None) is not None:
        warm_file = "/tmp/lambda-is-warm"
    elif os.getenv('OS', None) == 'WinNT':
        warm_file = "D:\\local\\temp\\"
    elif os.getenv('OS', None) == 'Windows_NT':
        warm_file = "D:\\local\\temp\\"
    elif os.getenv('NODE_ENV', None) == 'webtask':
        warm_file = "/tmp/lambda-is-warm"
    else:
        """If all else fails probably posix."""
        warm_file = "/tmp/lambda-is-warm"
    return warm_file


def is_warm():
    """Returns warm/not warm/not possible
       to denote if the aws lambda function is warm,
       as determined by whether or not warm_file() exists (warm/not warm)
       or if the filesystem is readonly (not possible)
    """
    if os.access(os.path.dirname(warm_file()), os.W_OK):
        if os.path.isfile(warm_file()):
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
            with open(warm_file(), 'a'):
                os.utime(warm_file(), None)
        except IOError as e:
            pass

def warm_since():
    """Return the date when the current warm version of the fn started.
    """
    if is_warm() == 'warm':
        ts = os.path.getmtime(warm_file())
        return ts


def warm_for():
    """Return the elapsed time that the fn has been warm for."""
    if is_warm() == 'warm':
        ts = os.path.getmtime(warm_file())
        warm_start = datetime.fromtimestamp(ts)
        now = datetime.now()
        return (now - warm_start).total_seconds()
    else:
        return 0
