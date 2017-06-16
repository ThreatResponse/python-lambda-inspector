import gzip
import json
try:
    import StringIO
except:
    from io import StringIO

try:
    import urllib2
except:
    import urllib.request as urllib2
import uuid

from os import getenv

def store_results_api(res):
    """Store Results via the API Component.

    Store results either in urllib2 or directly in s3 if lambda.
    HTTP request will be a POST instead of a GET when the data
    parameter is provided.
    """
    data = json.dumps(res)

    # Look for an environment variable containing the API key.
    # If it exists post the result to the API endpoint.
    api_key = getenv('observatory_api_key', None)
    headers = {
        "Authorization": "Basic %s" % api_key,
        'Content-Type': 'application/json'
        }
    if api_key is not None:
        req = urllib2.Request(
            'https://serverless-observatory.threatresponse.cloud/api/profile',
            data=data,
            headers=headers
        )
        try:
            response = urllib2.urlopen(req)
            return response.read()
        except Exception as e:
            pass
    else:
        return None

def store_results_s3(res):
    """
    Store results in s3.

    Assumes that we're in a lambda function (or something else with
    similar permissions).
    """
    s3_bucket = getenv('observatory-results-bucket', None)

    if s3_bucket is not None:
        # Only import boto3 if we need it.  Otherwise may not work all the time.
        import boto3

        s3 = boto3.client('s3')
        s3_name = "{name}.json.gz".format(name=uuid.uuid4().hex)

        # Compress the payload for fluentd friendlieness.
        data = compress_results(res)

        # Store the result in S3 bucket same as the API.
        try:
            response = s3.put_object(
                Key=s3_name,
                Body=data,
                Bucket=s3_bucket
            )
            return response
        except:
            pass
    else:
        return None


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
        return store_results_api(res)
    except Exception as e:
        return store_results_s3(res)
    finally:
        return None
