import launcher
import launcher
import unittest


class LauncherTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_runing_launcher(self):
        res = launcher.wrapper()
        assert res is not None

