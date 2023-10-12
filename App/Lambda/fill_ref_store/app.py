
import os
import boto3
import logging
import time
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    iam_role = os.environ['IAM_ROLE']
    ref_store = os.environ['REF_STORE']
    bucket = os.environ['BUCKET']

    omics = boto3.client('omics', region_name=os.environ['AWS_REGION'])
    key = event['Records'][0]['s3']['object']['key']
    bucket = event['Records'][0]['s3']['bucket']['name']

    logger.info(f'Starting reference import from: {bucket}/{key}')
    #Get filename without extension
    filename = os.path.splitext(os.path.basename(key))[0]

    job = omics.start_reference_import_job(
        referenceStoreId=ref_store, 
        roleArn=iam_role,
        sources=[{
            'sourceFile': f's3://{bucket}/{key}',
            'name': f'digitallab{filename}',
            'tags': {'SourceLocation': '1kg'}
        }])
    
    waiter = omics.get_waiter('reference_import_job_completed')
    waiter.wait(
        id=job['id'],
        referenceStoreId=ref_store
    )

    reference = omics.list_references(
        referenceStoreId=ref_store,
        filter={
            'name': "digitallab"+filename
        }
    )

    omics.create_variant_store(
        name='digitallab'+filename,
        reference={
            'referenceArn': reference['references'][0]['arn']
        }
    )

    return True 