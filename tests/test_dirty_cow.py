import pprint
from profilers.vulnerability import dirty_cow
import unittest


class DirtyC0WTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_setup(self):
        d = dirty_cow.DirtyC0W()
        res = d.setup()
        assert res is False
