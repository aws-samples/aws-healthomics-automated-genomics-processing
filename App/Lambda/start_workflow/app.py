import boto3
import logging
import os
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    omics = boto3.client('omics')
    params = event['run_params']
    params[0]['fastq_1'] = f's3://{os.environ["BUCKET"]}/{params[0]["source1"]}'
    params[0]['fastq_2'] = f's3://{os.environ["BUCKET"]}/{params[0]["source2"]}'
    params[0].pop('source1')
    params[0].pop('source2')
    params = {
        "sample_name": event['sample_name'],
        "fastq_pairs": params
            
    }

    response = omics.start_run(
       workflowId=event['workflow']['id'],
       workflowType=event['workflow']['type'],
       roleArn=event['iam_role'],
       parameters=params,
       outputUri=event['output_uri']
    )
    return response

