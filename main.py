import subprocess
import os

## General concept for now:
##
## 'lookups' is a dict that contains names of info
## and maps them to the functions to determine that info.
##
## 'wrapper' is a function that takes no args and calls
## the regular lambda start point for running the code locally.

## helpers

def call_shell_wrapper(args):
    """Intended to make it easy to add additional metrics from shell calls,
    such as capturing return values, etc.
    Currently no additional value.
    Subprocess module is recommended but didn't work for some uname calls.
    """
    return os.popen(" ".join(args)).read()
    # return subprocess.check_output(args)


def contents_of_file(fname):
    """Returns contents of file in a single string,
    or None if there is an IOError (eg. file not found).
    """
    try:
        with file(fname) as f:
            return f.read()
    except IOError:
        return None

## fns for specific pieces of data

def get_etc_issue():
    return contents_of_file("/etc/issue")

def get_pwd():
    return call_shell_wrapper(["pwd"])

def get_uname():
    return call_shell_wrapper(["uname", "-a"])

def get_env():
    return os.environ.__dict__.get('data')

## main map

lookups = {
    "/etc/issue": get_etc_issue,
    "pwd":        get_pwd,
    "uname":      get_uname,
    "env":        get_env
}

def make_result_dict(d):
    """Given the lookups dict (strings to fns),
    will return the dictionary with fns replaced by the results of
    calling them.
    """
    return {k: v() for (k,v) in d.iteritems()}

def lambda_handler(event, context):
    return make_result_dict(lookups)

def wrapper():
    """Helper for easily calling this from a command line locally
    like `python -c 'import main; main.wrapper()'`
    """
    res = lambda_handler(None, None)
    print res
    return res
