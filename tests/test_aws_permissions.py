import pprint
from profilers.aws import permissions
from moto import mock_cloudwatch, mock_ec2, mock_sqs
import unittest


class AWSPermissionsTest(unittest.TestCase):
    def setUp(self):
        pass

    @mock_cloudwatch
    def test_cloudwatch_permissions(self):
        check = permissions.check_cloudwatch()
        assert check['CreateLogGroup'] is not None
        assert check['CreateLogStream'] is not None
        assert check['PutLogEvents'] is not None

    @mock_ec2
    def test_ec2_permissions(self):
        check = permissions.check_ec2()
        assert check['DescribeTags'] is not None

    @mock_sqs
    def test_sqs_permissions(self):
        check = permissions.check_sqs()
        assert check['ListQueues'] is not None
        assert check ['PutMessage'] is not None