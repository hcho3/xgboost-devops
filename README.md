# xgboost-devops
DevOps / Continuous Integration tools for XGBoost project

## Cost Watcher (WIP)
[![Deploy lambda](https://github.com/hcho3/xgboost-devops/workflows/Deploy%20lambda/badge.svg?branch=mainline)](https://github.com/hcho3/xgboost-devops/actions?query=workflow%3A%22Deploy+lambda%22)

* Test `lambda_function.py` locally by running `local_runner.py`.
* Run `deploy.py` to deploy `lambda_function.py` as the AWS Lambda function `XGBoostCICostWatcher`.
