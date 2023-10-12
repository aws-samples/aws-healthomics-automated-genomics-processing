import json
import boto3
import botocore
import logging
import uuid
import os


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    print (event['Records'][0]['s3'])
    data = event['Records'][0]['s3']
    s3r = boto3.resource('s3')
    omics = boto3.client('omics', region_name=os.environ['AWS_REGION'])
    bucket = data['bucket']['name']
    metadatafile_key = data['object']['key']
    
    logger.info(f'Reading {metadatafile_key} from bucket {bucket}')
    obj = s3r.Object(bucket, metadatafile_key)
    
    metadata = json.loads(obj.get()['Body'].read().decode('utf-8'))
    for f in metadata['run_params']:
        checkFile(bucket, f['source1'])
        checkFile(bucket, f['source2'])
    
    try:
        reference = omics.list_references(
            referenceStoreId=os.environ['REF_STORE'],
            filter={
                'name': metadata['reference_genome']
            }
        )
        
        data = {
            "validationFailed": False,
            "id": uuid.uuid4().hex,
            "name": metadata['name'],
            "description": metadata['description'] if metadata['description'] else "",
            "sequencer_platform": metadata['sequencer_platform'],
            "input_path": metadata['input_path'],
            "reference_genome": reference['references'][0]['id'],
            "ref_arn": reference['references'][0]['arn'],
            "sample_name": uuid.uuid4().hex,
            "subject_id": metadata['run_params'][0]['read_group'],
            "workflow": metadata['workflow'],
            "iam_role": os.environ['IAM_ROLE'],
            "ref_store": os.environ['REF_STORE'],
            "seq_store": os.environ['SEQ_STORE'],
            "output_uri": "s3://"+os.environ['BUCKET']+"/out",
            "bucket": os.environ['BUCKET'],
            "run_params": metadata['run_params'],
            "var_store": metadata['reference_genome']
        }
        
        #Start statemachine with boto3
        client = boto3.client('stepfunctions')
        client.start_execution(
            stateMachineArn=os.environ['STATE_MACHINE'],
            input=json.dumps(data)
        )
        
        return True
    except Exception as e:
        logger.error("Could not map metadata to the schema")
        logger.error(str(e))
        raise e


def checkFile(bucket,f):
    s3c = boto3.client('s3')
    try:
        logger.info(f'Checking on file {f}')
        s3c.head_object(Bucket=bucket, Key=f)
    except botocore.exceptions.ClientError as e:
        logger.error(f'File {f} not found')
        if e.response['Error']['Code'] == "404":
            logger.error("File not found")
        elif e.response['Error']['Code'] == 403:
            logger.error("Unauthorized to check bucket or key")
        raise e