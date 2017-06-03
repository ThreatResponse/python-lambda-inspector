import json
import urllib2
import uuid
import gzip
import StringIO

def store_results_api(res):
    """Store Results via the API Component.

    HTTP request will be a POST instead of a GET when the data
    parameter is provided.
    """
    data = json.dumps(res)

    headers = {'Content-Type': 'application/json'}

    req = urllib2.Request(
        'https://67bfbz4uig.execute-api.us-west-2.amazonaws.com/dev/',
        data=data,
        headers=headers
    )
    try:
        response = urllib2.urlopen(req)
        print response.read()
        return response.read()
    except Exception as e:
        raise e

def store_results_s3(res):
    """
    Store results in s3.

    Assumes that we're in a lambda function (or something else with
    similar permissions).
    """

    # Only import boto3 if we need it.  Otherwise may not work all the time.
    import boto3

    s3 = boto3.client('s3')
    s3_name = "{name}.json.gz".format(name=uuid.uuid4().hex)
    s3_bucket = 'threatresponse.showdown'

    # Compress the payload for fluentd friendlieness.
    data = compress_results(res)

    # Store the result in S3 bucket same as the API.
    response = s3.put_object(
        Key=s3_name,
        Body=data,
        Bucket=s3_bucket
    )
    return response


def compress_results(res):
    out = StringIO.StringIO()
    file_content = json.dumps(res)
    with gzip.GzipFile(fileobj=out, mode="w") as f:
        f.write(file_content)
    return out.getvalue()


def store_results(res):
    """
    Attempts to store results via POST, falls back to writing directly to S3.
    """
    try:
        store_results_api(res)
    except Exception as e:
        store_results_s3(res)
