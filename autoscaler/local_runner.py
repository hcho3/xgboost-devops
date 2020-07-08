import lambda_function
import logging

logging.basicConfig(level=logging.INFO)
print(lambda_function.lambda_handler(None, None))
