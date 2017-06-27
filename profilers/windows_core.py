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

