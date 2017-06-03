"""
python-lambda-inspector
General concept for now:
    'lookups' is a dict that contains names of info
    and maps them to the functions to determine that info.
    'wrapper' is a function that takes no args and calls
    the regular lambda start point for running the code locally.
    Now with CI goodness in us-west-2.
"""

class Profiler(object):

    """Main map table of items to post or store."""
    lookups = {}
    
    @classmethod
    def run(cls):
        raise Exception("Implement this method!")
