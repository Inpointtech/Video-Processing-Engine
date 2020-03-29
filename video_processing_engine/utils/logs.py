"""Utility for replacing prints with logs which make sense."""

import logging
import os
import sys
from pathlib import Path

from video_processing_engine.utils.paths import logs as _logs


def log(file: str, level: str = 'debug') -> logging.Logger:
  """Create log file and log print events.

  Args:
    file: Current file name.
    level: Logging level.

  Returns:
    Logger object which records logs in ./logs/ directory.
  """
  logger = logging.getLogger(file)
  logger.setLevel(f'{level.upper()}')
  name = f'{Path(file.lower()).stem}.log'
  name = Path(os.path.join(_logs, name))
  custom_format = ('%(asctime)s.%(msecs)04d    %(levelname)-8s    '
                   '%(filename)s:%(lineno)-15s    %(message)s')
  formatter = logging.Formatter(custom_format, '%Y-%m-%d %H:%M:%S')
  # Create log file.
  file_handler = logging.FileHandler(os.path.join(_logs, name))
  file_handler.setFormatter(formatter)
  logger.addHandler(file_handler)
  # Print log statement.
  stream_handler = logging.StreamHandler(sys.stdout)
  stream_handler.setFormatter(formatter)
  logger.addHandler(stream_handler)
  # Return logger object.
  return logger
