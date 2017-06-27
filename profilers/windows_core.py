import os
import pkgutil
import calendar
import copy
import pkg_resources
import platform
import socket

from collections import OrderedDict
from datetime import datetime, timedelta
from profilers import is_warm

from profilers.profiler_base import Profiler
from profilers.utils import call_shell_wrapper, call_powershell_wrapper, contents_of_file, make_result_dict


class WindowsCoreProfiler(Profiler):

    """Functions for specific data retreival."""

    def get_pwd():
        return call_powershellshell_wrapper(['Convert-Path', '.'])

    def get_release_version():
        return platform.release()


    def get_df():
        return call_powershellshell_wrapper(
            ["Get-PSDrive", "-psprovider", "FileSystem", "|", "Select-Object",
             "-Property", "*"]
        )

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
        return call_powershell_wrapper(["Get-Process", "|", "ConvertTo-Json"])

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
        "pwd":        get_pwd,
        "release":    get_release_version,
        "df":         get_df,
        "is_warm":    is_warm.is_warm,
        "warm_since": is_warm.warm_since,
        "warm_for":   is_warm.warm_for,
        "package_count": get_package_count,
        "packages":   get_packages,
        "package_versions": get_package_versions,
        "ps":         get_processes,
        "timestamp":  get_timestamp,
        "ipaddress":  get_ipaddress,
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
