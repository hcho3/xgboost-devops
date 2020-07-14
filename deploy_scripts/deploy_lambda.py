import os
import shutil
import glob
import argparse

import boto3

def deploy_lambda(lambda_function, code_dir):
    os.makedirs('codepkg')
    for p in glob.glob(os.path.join(code_dir, '*.py')):
        print(f'Packaging {p}')
        shutil.copy(p, 'codepkg')
    shutil.make_archive('codepkg', format='zip', root_dir='codepkg', base_dir='.')
    shutil.rmtree('codepkg')
    print(f'Deploying to Lambda function {lambda_function}...')
    client = boto3.client('lambda', region_name='us-west-2')
    with open('codepkg.zip', 'rb') as f:
        r = client.update_function_code(
            FunctionName=lambda_function,
            ZipFile=f.read(),
            Publish=False)
    print(f'Finished deploying to Lambda function {lambda_function}.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script to deploy a Lambda function')
    parser.add_argument('--lambda-function', type=str, help='Name of the AWS Lambda function',
            required=True)
    parser.add_argument('--code-dir', type=str,
            help='Directory containing Python code for the Lambda function', required=True)
    args = parser.parse_args()
    deploy_lambda(args.lambda_function, args.code_dir)
