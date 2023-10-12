import json
import boto3
import os
import sys
import logging
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    downloadFile(event['Bucket'], event['Key'], event['Name'])
    uploadFile(event['Name'])

def downloadFile(bucket, key,name):
    s3 = boto3.client('s3')
    s3.download_file(bucket, key, '/tmp/' + name)   

def uploadFile(filename):
    params = getParams()

    url = params["BaseURL"] + "/v1/data-acquisition/agent/upload?file=sampleFile.txt&agentId=650c7317-4286-4006-b2d7-003811a43661&sourceType=unknown"
    payload = {'agentId': '650c7317-4286-4006-b2d7-003811a43661',
                'filePath': filename,
                'fileCategory': 'PROCESSED'}
    files=[
      ('file',('file',open('/tmp/'+filename,'rb'),'application/octet-stream'))
    ]
                
    headers = {
        'x-org-slug': params["OrgSlug"],
        'Authorization': 'Bearer '+params["JWT"]
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload, files=files)
        logging.info(response.text)
    except Exception as e:
        logging.error("Error connecting to TDP API")
        logging.error(e)
        sys.exit(0)

    if response.status_code != 200:
        logging.error(f'Error connecting to TDP API. Status code: {response.status_code}')
        sys.exit(0)
    return True


def getParams():
    ## Return the parameters from SSM for the application
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=os.environ['TETRA_SECRETS'])
    return json.loads(response['SecretString'])
