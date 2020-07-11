import lambda_function
import logging

logging.basicConfig(level=logging.INFO)
logging.info(lambda_function.lambda_handler(None, None))
