import os
import pkgutil
import calendar
import copy
import pkg_resources
import platform
import socket
from socket import socket, AF_INET, SOCK_DGRAM
import re
import struct
import time

from contextlib import closing
from collections import OrderedDict
from datetime import datetime, timedelta
from profilers import is_warm

from profilers.profiler_base import Profiler
from profilers.utils import call_shell_wrapper, contents_of_file, make_result_dict
from profilers.posix_permissions import PosixPermissions


class PosixCoreProfiler(Profiler):

    """Functions for specific data retreival."""

    def check_time_drift():
        ## Ignores network latency to the NTP server.

        NTP_PACKET_FORMAT = "!12I"
        NTP_DELTA = 2208988800L # 1970-01-01 00:00:00
        NTP_QUERY = '\x1b' + 47 * '\0'
        host = "pool.ntp.org"
        port = 123

        with closing(socket(AF_INET, SOCK_DGRAM)) as s:
            s.sendto(NTP_QUERY, ("pool.ntp.org", 123))
            msg, address = s.recvfrom(1024)
            local_time = time.time()
        unpacked = struct.unpack(NTP_PACKET_FORMAT,
                       msg[0:struct.calcsize(NTP_PACKET_FORMAT)])
        ntp_time = unpacked[10] + float(unpacked[11]) / 2**32 - NTP_DELTA

        return abs(ntp_time - local_time)

    def check_interesting_env_vars():
        ## Returns a subset of environment variables that are interesting:
        ## secrets, etc.
        
        interesting_vars = [
            'AWS_SESSION_TOKEN',
            'AWS_SECURITY_TOKEN',
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
        ]

        env_vars = os.environ.__dict__
        interesting_subset = dict((k, env_vars[k]) for k in interesting_vars if k in env_vars)
        
        return interesting_subset
    
    def check_env_editable():
        os.environ['profiler_test'] = 'flag'

        ## we check with a different method to demonstrate that it's not
        ## just edited within 'environ'
        res = call_shell_wrapper(['env | grep \'profiler_test\''])

        if res == 'profiler_test=flag\n':
            return True
        else:
            return False
    
    def check_source_editable():
        ## check if we can edit the file on disk
        flag_string = 'profiler_test'
        
        call_shell_wrapper(['echo "{}" >> {}'.format(flag_string, __file__)])
        res = call_shell_wrapper(['tail -n 1 {}'.format(__file__)])

        if res == '{}\n'.format(flag_string):
            return True
        else:
            return False

    def check_arbitrary_binary():
        ## Re: Lambda
        ## I wasn't able to get executable permissions on the binary in the code dir
        ## and didn't have permissions to edit with chmod.
        ## We just attach a precompiled binary, move it to /tmp, and execute.
        
        call_shell_wrapper(['mv profiler_bin /tmp'])
        call_shell_wrapper(['chmod +x /tmp/profiler_bin'])
        res = call_shell_wrapper(['/tmp/profiler_bin'])

        if res == 'custom profiler binary':
            return True
        else:
            return False
    
    def check_other_runtimes():
        ## for now, just node.  Can expand as wanted, thus we return a dict.

        node_test = call_shell_wrapper(['node -e \'console.log("foo");\''])

        if node_test == 'foo\n':
            return {'node': True}
        else:
            return {'node': False}
            
    
    def check_docker_containers():
        docker_socket_locations = ["/var/run/docker.sock"]

        results = [os.path.exists(f) for f in docker_socket_locations]

        return any(results)

    def check_capabilities():
        ## we assume (checked on lambda) that we are PID 1
        ## see http://man7.org/linux/man-pages/man5/proc.5.html
        ## If we can't check permissions, we assume none.
        
        statline = call_shell_wrapper(["grep 'CapEff' /proc/1/status"])
        flags = 0

        if statline:
            bitmask = re.match(r'CapEff:\t(\d+)\n', statline).groups()

            if len(bitmask) == 1:
                flags = int(bitmask[0])

        return flags

    def get_pwd():
        return call_shell_wrapper(["pwd"])

    def get_release_version():
        return platform.release()

    def get_uptime():
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                uptime_string = str(timedelta(seconds=uptime_seconds))
                return uptime_string
        except IOError:
            return ""

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

    def get_package_versions():
        results = {}
        for x in pkgutil.iter_modules():
            try:
                results[x[1]] = {
                    'version': str(pkg_resources.get_distribution(x[1]).version)
                }
            except:
                pass
        return results

    def get_package_count():
        return len([x[1] for x in pkgutil.iter_modules()])

    def get_processes():
        return call_shell_wrapper(["ps", "aux"])

    def get_timestamp():
        return calendar.timegm(datetime.utcnow().utctimetuple())

    def get_ipaddress():
        # http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib/25850698#25850698
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
        "package_versions": get_package_versions,
        "ps":         get_processes,
        "timestamp":  get_timestamp,
        "ipaddress":  get_ipaddress,
        "uptime":     get_uptime,
        "time_drift": check_time_drift,
        "env_subset": check_interesting_env_vars,
        "source_editable": check_source_editable,
        "other_runtimes": check_other_runtimes,
        "docker_sockets": check_docker_containers,
        "proc_capabilities": check_capabilities,
        "permissions": PosixPermissions().most_writable_paths
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
