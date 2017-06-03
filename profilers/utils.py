import os

def call_shell_wrapper(args):
    """
    Intended to make it easy to add additional metrics from shell calls,
    such as capturing return values, etc.
    Currently no additional value.
    Subprocess module is recommended but didn't work for some uname calls.
    """
    return os.popen(" ".join(args)).read()


def contents_of_file(fname):
    """Return contents of file in a single string.

    Return None if there is an IOError (eg. file not found).
    """

    try:
        with file(fname) as f:
            return f.read()
    except IOError:
        return None

def get_sandbox():
    """Function to try and determine what runtime we are in.

    We try our best to provide this in the SANDBOX_RUNTIME env var.
    """

    return os.getenv('SANDBOX_RUNTIME', 'unknown')

def make_result_dict(d):
    """Create dictionary of results.

    Given the lookups dict (strings to fns),
    will return the dictionary with fns replaced by the results of
    calling them.
    """
    return {k: v() for (k, v) in d.iteritems()}

def run_profiler(env):
    res = make_result_dict(lookups)

    res['sandbox'] = env

    return res
