import os
import is_warm
import pkgutil
import json
import calendar
import copy
import platform
import socket

from collections import OrderedDict
from datetime import datetime

from utils import call_shell_wrapper, contents_of_file, make_result_dict


"""
python-lambda-inspector
General concept for now:
    'lookups' is a dict that contains names of info
    and maps them to the functions to determine that info.
    'wrapper' is a function that takes no args and calls
    the regular lambda start point for running the code locally.
    Now with CI goodness in us-west-2.
"""

"""Functions for specific data retreival."""


def get_pwd():
    return call_shell_wrapper(["pwd"])


def get_release_version():
    return platform.release()

def get_env():
    return copy.deepcopy(os.environ.__dict__.get('data'))


def get_df():
    return call_shell_wrapper(["df", "-h"])


def get_cpuinfo():
    ''' Return the information in /proc/cpuinfo
    as a dictionary in the following format:
    cpu_info['proc0']={...}
    cpu_info['proc1']={...}

    '''
    cpuinfo = OrderedDict()
    procinfo = OrderedDict()

    nprocs = 0
    try:
        with open('/proc/cpuinfo') as f:
            for line in f:
                if not line.strip():
                    # end of one processor
                    cpuinfo['proc%s' % nprocs] = procinfo
                    nprocs = nprocs+1
                    # Reset
                    procinfo = OrderedDict()
                else:
                    if len(line.split(':')) == 2:
                        procinfo[
                            line.split(':')[0].strip()
                        ] = line.split(':')[1].strip()
                    else:
                        procinfo[line.split(':')[0].strip()] = ''
    except Exception as e:
        """Currently only works for posix."""
        pass
    return cpuinfo


def get_meminfo():
    ''' Return the information in /proc/meminfo
    as a dictionary '''

    meminfo = OrderedDict()
    try:
        with open('/proc/meminfo') as f:
            for line in f:
                meminfo[line.split(':')[0]] = line.split(':')[1].strip()
    except Exception as e:
        """Currently only works for posix."""
        pass
    return meminfo


def get_packages():
    return [x[1] for x in pkgutil.iter_modules()]


def get_package_count():
    return len([x[1] for x in pkgutil.iter_modules()])


def get_processes():
    return call_shell_wrapper(["ps", "aux"])


def truncate(string, start=0, end=0):
    return string[start:end]


def get_timestamp():
    return calendar.timegm(datetime.utcnow().utctimetuple())

def get_ipaddress():
    #http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib/25850698#25850698
    local_ip_address='0.0.0.0'
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 53))
        local_ip_address = s.getsockname()[0]
    except Exception as e:
        pass
    return local_ip_address


"""Main map table of items to post or store."""
lookups = {
    # "/etc/issue": get_etc_issue,
    "pwd":        get_pwd,
    # "uname":      get_uname,
    "release":    get_release_version,
    "env":        get_env,
    "df":         get_df,
    "is_warm":    is_warm.is_warm,
    "warm_since": is_warm.warm_since,
    "warm_for":   is_warm.warm_for,
    # "dmesg":      get_dmesg,
    "cpuinfo":    get_cpuinfo,
    "meminfo":    get_meminfo,
    "package_count": get_package_count,
    "packages":   get_packages,
    "ps":         get_processes,
    "timestamp":  get_timestamp,
    "ipaddress":  get_ipaddress
}

"""Remove any sensitive information about the account here."""
sanitize_envvars = {
    "AWS_SESSION_TOKEN":
        {
            "func": truncate, "args": [], "kwargs": {'end': 12}
        },
    "AWS_SECURITY_TOKEN":
        {
            "func": truncate, "args": [], "kwargs": {'end': 12}
        },
    "AWS_ACCESS_KEY_ID":
        {
            "func": truncate, "args": [], "kwargs": {'end': 12}
        },
    "AWS_SECRET_ACCESS_KEY":
        {
            "func": truncate, "args": [], "kwargs": {'end': 12}
        }
}


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

def run_profiler(env):
    res = make_result_dict(lookups)

    is_warm.mark_warm()

    res = sanitize_env(res)
    res['sandbox'] = env

    return jsonify_results(res)
