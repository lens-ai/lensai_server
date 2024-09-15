# logger.py
import logging
import sys

def setup_logger():
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Info level logging to stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(log_formatter)

    # Error level logging to stderr
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(log_formatter)

    # Apply handlers to the root logger
    logging.basicConfig(level=logging.INFO, handlers=[stdout_handler, stderr_handler])

    # Optional: Return the logger instance if needed
    logger = logging.getLogger()
    return logger
