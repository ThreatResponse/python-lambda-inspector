from utils import call_shell_wrapper, contents_of_file, make_result_dict

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

def run_profiler(env):
    res = make_result_dict(lookups)

    res['sandbox'] = env

    return res
