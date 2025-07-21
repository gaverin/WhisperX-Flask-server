import os
import logging
from datetime import datetime


class Logger():

    def __init__(self, dir_path):
        self._dir_path = dir_path
        # disable flask logger
        werkzeug = logging.getLogger('werkzeug')
        werkzeug.disabled = True


    def log(self, msg: str):
        now = datetime.now()
        year = now.strftime('%Y')
        month = now.strftime('%m')

        # Create the folder structure: logs/<year>/<month>
        log_dir = os.path.join(self._dir_path, year, month)
        os.makedirs(log_dir, exist_ok=True)  # Ensure the directory exists

        # Define the log file path
        log_file = os.path.join(log_dir, f"{month}-{year}.log")

        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),  # Log to the file
            ]
        )

        # Add log
        logging.info(msg)