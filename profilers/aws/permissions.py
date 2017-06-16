import botocore
import boto3
import os
import time
import uuid



"""
Checks to run if the environment is AWS.

logs:CreateLogGroup
logs:CreateLogStream
logs:PutLogEvents
ec2:DescribeTags
sqs:ListQueues
sqs:PutMessage

"""

def _cloudwatch_create_log_group(client):
    try:
        response = client.create_log_group(
            logGroupName="serverless-observatory-check-{uuid}".format(uuid=uuid.uuid4().hex),
        )
        return True
    except botocore.exceptions.ClientError as e:
        return False

def _cloudwatch_create_log_stream(client):
    try:
        response = client.create_log_stream(
            logGroupName=os.getenv('AWS_LAMBDA_LOG_GROUP_NAME', None),
            logStreamName='foo'
        )
        return True
    except botocore.exceptions.ClientError as e:
        return False

def _cloudwatch_put_log_events(client):
    try:
        response = client.put_log_events(
            logGroupName=os.getenv('AWS_LAMBDA_LOG_GROUP_NAME', None),
            logStreamName=os.getenv('AWS_LAMBDA_LOG_STREAM_NAME', None),
            logEvents=[
                {
                    'timestamp': int(time.time()),
                    'message': 'Test event from the serverless observatory profiler.'
                },
            ]
        )
    except botocore.exceptions.ClientError as e:
        return False

def check_cloudwatch():
    cloudwatch = boto3.client('logs')
    results = {
        'CreateLogGroup': _cloudwatch_create_log_group(cloudwatch),
        'CreateLogStream': _cloudwatch_create_log_group(cloudwatch),
        'PutLogEvents': _cloudwatch_put_log_events(cloudwatch)
    }
    return results

def _ec2_can_describe_tags(client):
    try:
        response = client.describe_tags(
            DryRun=True,
            MaxResults=10
        )
        return True
    except botocore.exceptions.ClientError as e:
        return False

def check_ec2():
    ec2 = boto3.client('ec2', region_name=os.getenv('AWS_DEFAULT_REGION'))
    results = {
        'DescribeTags': _ec2_can_describe_tags(ec2)
    }
    return results

def _sqs_can_list_queues(client):
    try:
        response = client.list_queues()
        return True
    except botocore.exceptions.ClientError as e:
        return False

def _sqs_can_put_message(client):
    try:
        response = client.list_queues()

        if response.get('QueueUrls', None) is not None:
            for queue in response['QueueUrls']:
                try:
                    client.send_message(
                        QueueUrl=queue,
                        MessageBody={}
                    )
                    # Set status to pass first put that succeeds
                    return True
                    break
                except:
                    # Allow loop to continue
                    pass
            return False
        else:
            return False
    except botocore.exceptions.ClientError as e:
        return False

def check_sqs():
    sqs = boto3.client('sqs')
    results = {
        'ListQueues': _sqs_can_list_queues(sqs),
        'PutMessage': _sqs_can_put_message(sqs)
    }
    return results
