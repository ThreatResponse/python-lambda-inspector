from profiler_base import Profiler
from utils import call_shell_wrapper, contents_of_file, make_result_dict


class PosixExtraProfiler(Profiler):

    def get_etc_issue():
        return contents_of_file("/etc/issue")

    def get_uname():
        return call_shell_wrapper(["uname", "-a"])

    def get_dmesg():
        return call_shell_wrapper(["dmesg"])

    lookups = {
        "/etc/issue": get_etc_issue,
        "uname":      get_uname,
        "dmesg":      get_dmesg
    }

    @classmethod
    def run(cls):
        res = make_result_dict(cls.lookups)

        return res
        
