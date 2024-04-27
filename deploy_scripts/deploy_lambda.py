import argparse
import glob
import os
import shutil

import boto3


def deploy_lambda(lambda_function, code_dir):
    # Package code
    os.makedirs("codepkg")
    for p in glob.glob(os.path.join(code_dir, "*.py")):
        print(f"Packaging {p}")
        shutil.copy(p, "codepkg")
    print(f"Packaging metadata.ini")
    shutil.copy("metadata.ini", "codepkg")
    shutil.make_archive("codepkg", format="zip", root_dir="codepkg", base_dir=".")
    shutil.rmtree("codepkg")

    # Re-create lambda and deploy code package
    client = boto3.client("lambda", region_name="us-west-2")
    print(f"Re-creating Lambda function {lambda_function}...")
    try:
        client.get_function(FunctionName=lambda_function)
        client.delete_function(FunctionName=lambda_function)
    except client.exceptions.ResourceNotFoundException:
        pass
    print(f"Deploying to Lambda function {lambda_function}...")
    with open("codepkg.zip", "rb") as f:
        client.create_function(
            FunctionName=lambda_function,
            Runtime="python3.12",
            Role="arn:aws:iam::492475357299:role/XGBoost-CI-Lambda",
            Handler="lambda_function.lambda_handler",
            Code={"ZipFile": f.read()},
            Timeout=300,
            MemorySize=128,
            Publish=False,
            PackageType="Zip",
            Architectures=["x86_64"],
        )
    waiter = client.get_waiter("function_exists")
    waiter.wait(FunctionName=lambda_function)
    print(f"Finished deploying to Lambda function {lambda_function}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to deploy a Lambda function")
    parser.add_argument(
        "--lambda-function",
        type=str,
        help="Name of the AWS Lambda function",
        required=True,
    )
    parser.add_argument(
        "--code-dir",
        type=str,
        help="Directory containing Python code for the Lambda function",
        required=True,
    )
    args = parser.parse_args()
    deploy_lambda(args.lambda_function, args.code_dir)
