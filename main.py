import subprocess
import os
import is_warm
import pkgutil
import json
import calendar
import urllib
import urllib2


from datetime import datetime



## General concept for now:
##
## 'lookups' is a dict that contains names of info
## and maps them to the functions to determine that info.
##
## 'wrapper' is a function that takes no args and calls
## the regular lambda start point for running the code locally.

## Now with CI goodness in us-west-2

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

def get_df():
    return call_shell_wrapper(["df", "-h"])

def get_dmesg():
    return call_shell_wrapper(["dmesg"])

def get_cpuinfo():
    return contents_of_file("/proc/cpuinfo")

def get_packages():
    return [x[1] for x in pkgutil.iter_modules()]

def get_processes():
    return call_shell_wrapper(["ps", "aux"])

def truncate(string, start=0, end=0):
    return string[start:end]

def get_timestamp():
    return calendar.timegm(datetime.utcnow().utctimetuple())

## main map

lookups = {
    "/etc/issue": get_etc_issue,
    "pwd":        get_pwd,
    "uname":      get_uname,
    "env":        get_env,
    "df":         get_df,
    "is_warm":    is_warm.is_warm,
    "warm_since": is_warm.warm_since,
    "warm_for":   is_warm.warm_for,
    "dmesg":      get_dmesg,
    "cpuinfo":    get_cpuinfo,
    "packages":   get_packages,
    "ps":         get_processes,
    "timestamp":  get_timestamp
}

sanitize_envvars = {
    "AWS_SESSION_TOKEN": {"func": truncate, "args": [], "kwargs": {'end': 12}},
    "AWS_SECURITY_TOKEN": {"func": truncate, "args": [], "kwargs": {'end': 12}},
    "AWS_ACCESS_KEY_ID": {"func": truncate, "args": [], "kwargs": {'end': 12}},
    "AWS_SECRET_ACCESS_KEY": {"func": truncate, "args": [], "kwargs": {'end': 12}}
}

def make_result_dict(d):
    """Given the lookups dict (strings to fns),
    will return the dictionary with fns replaced by the results of
    calling them.
    """
    return {k: v() for (k,v) in d.iteritems()}

def sanitize_env(d):
    for var, action in sanitize_envvars.iteritems():
        try:
            sanitize_func = action['func']
            args = [d['env'][var]] + action['args']
            kwargs = action['kwargs']
            d['env'][var] = sanitize_func(*args, **kwargs)
        except KeyError:
            pass

    return d

def jsonify_results(d):
    if 'warm_since' in d:
        d['warm_since'] = str(d['warm_since'])
    if 'warm_for' in d:
        d['warm_for'] = str(d['warm_for'])

    return d

def store_results(res):
    """
        Store results either in urllib2 or directly in s3 if lambda.
        HTTP request will be a POST instead of a GET when the data
        parameter is provided.
    """
    print res
    data =  json.dumps(res)

    headers = {'Content-Type': 'application/json'}

    req = urllib2.Request(
        'https://showdown-api.ephemeralsystems.com/',
        data=data,
        headers=headers
    )

    response = urllib2.urlopen(req)

    return response.read()

def lambda_handler(event, context):
    res = make_result_dict(lookups)

    is_warm.mark_warm()

    #sanitize results
    res=sanitize_env(res)

    #send results to API
    api_call = store_results(res)
    print api_call
    #post results
    #print(res)

    return jsonify_results(res)

def wrapper():
    """Helper for easily calling this from a command line locally
    like `python -c 'import main; main.wrapper()' | jq '.'`
    """
    res = lambda_handler(None, None)
    #print json.dumps(res)
    return res
