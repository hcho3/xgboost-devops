import logging

import lambda_function

logging.basicConfig(level=logging.INFO)
logging.info(lambda_function.lambda_handler(None, None))
