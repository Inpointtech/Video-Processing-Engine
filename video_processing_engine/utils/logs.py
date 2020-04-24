"""Utility for replacing prints with logs which make sense."""

import logging
import os
import sys
import time
from pathlib import Path

from video_processing_engine.utils.paths import logs as _logs


class TimeFormatter(logging.Formatter):

  def formatTime(self, record, datefmt=None):
    convert = self.converter()
    if datefmt:
      if '%F' in datefmt:
        msec = '%03d' % record.msecs
        datefmt = datefmt.replace('%F', msec)
      string = time.strftime(datefmt, convert)
    else:
      temp = time.strftime('%Y-%m-%d %H:%M:%S', convert)
      string = '%s.%03d' % (temp, record.msecs)
    return string


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
  custom_format = ('%(asctime)s    %(levelname)-8s    '
                   '%(filename)s:%(lineno)-15s    %(message)s')
  formatter = TimeFormatter(custom_format, '%Y-%m-%d %H:%M:%S.%F %Z')
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
