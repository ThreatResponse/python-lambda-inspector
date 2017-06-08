import os
import is_warm
import pkgutil
import json
import calendar
import copy
import platform
import socket
import re

from collections import OrderedDict
from datetime import datetime

from profiler_base import Profiler
from utils import call_shell_wrapper, contents_of_file, make_result_dict


class PosixCoreProfiler(Profiler):

    """Functions for specific data retreival."""

    def check_docker_containers():
        docker_socket_locations = ["/var/run/docker.sock"]

        results = [os.path.ispath(f) for f in docker_socket_locations]

        return any(results)

    def check_capabilities():
        ## we assume (checked on lambda) that we are PID 1
        ## see http://man7.org/linux/man-pages/man5/proc.5.html
        ## If we can't check permissions, we assume none.
        
        statline = call_shell_wrapper(["grep 'CapEff' /proc/1/status"])

        bitmask = re.match(r'CapEff:\t(\d+)\n', res).groups()
        flags = 0

        if len(bitmask) == 1:
            flags = int(bitmask[0])

        return flags

    def get_pwd():
        return call_shell_wrapper(["pwd"])

    def get_release_version():
        return platform.release()

    def get_env():
        """Remove any sensitive information about the account here."""

        def truncate(string, start=0, end=0):
            return string[start:end]
        
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

        env_vars = copy.deepcopy(os.environ.__dict__.get('data'))

        for var, action in sanitize_envvars.iteritems():
            try:
                sanitize_func = action['func']
                args = [env_vars[var]] + action['args']
                kwargs = action['kwargs']
                env_vars[var] = sanitize_func(*args, **kwargs)
            except KeyError:
                pass

        return env_vars
        

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

    @staticmethod
    def jsonify_results(d):
        if 'warm_since' in d:
            d['warm_since'] = str(d['warm_since'])
        if 'warm_for' in d:
            d['warm_for'] = str(d['warm_for'])

        return d

    @classmethod
    def run(cls):
        res = make_result_dict(cls.lookups)

        import pdb
        # pdb.set_trace()
        is_warm.mark_warm()

        return cls.jsonify_results(res)
