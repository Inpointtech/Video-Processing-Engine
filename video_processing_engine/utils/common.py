"""Utility for performing common functions."""

import os
import socket
import subprocess
from datetime import datetime
from typing import Optional, Union

# TODO(xames3): Remove suppressed pyright warnings.
# pyright: reportMissingTypeStubs=false
from video_processing_engine.vars import dev


def check_internet(timeout: Optional[Union[float, int]] = 10.0) -> bool:
  """Check the internet connectivity."""
  # You can find the reference code here:
  # https://gist.github.com/yasinkuyu/aa505c1f4bbb4016281d7167b8fa2fc2
  try:
    socket.create_connection((dev.PING_URL, dev.PING_PORT), timeout=timeout)
    return True
  except OSError:
    pass
  return False


def now() -> datetime:
  """Return current time without microseconds."""
  return datetime.now().replace(microsecond=0)


def toast(title: str, message: str) -> None:
  """Display toast message.

  Displays toast message on Darwin based system and prints toast on
  Windows machines.

  Args:
    title: Title message of the toast.
    message: Message to be displayed.

  Notes:
    This function needs to be used only for the purpose of debugging
    code. Kindly use sparingly.

  TODO(xames3): Add support for Windows based notifications.
  """
  if os.name == 'nt':
    print(f'{title}:\n{message}')
  else:
    subprocess.call(['notify-send', title, message])


def convert_bytes(number: Union[float, int]) -> Optional[str]:
  """Converts the number into size denominations.

  This function will convert bytes to KB, MB, GB, etc.

  Args:
    number: Number to be converted into file size.

  Returns:
    File size denomation.
  """
  for idx in ['bytes', 'KB', 'MB', 'GB', 'TB']:
    if number < 1024.0:
      return '%3.1f %s' % (number, idx)
    number /= 1024.0


def file_size(path: str) -> Optional[str]:
  """Return the file size."""
  if os.path.isfile(path):
    return convert_bytes(os.stat(path).st_size)


def timestamp_dirname(ts_format: str = '%d_%m_%Y_%H_%M_%S') -> str:
  """Returns current time in a timestamp format."""
  return str(now().strftime(ts_format))


def calculate_duration(start_time: str,
                       end_time: str,
                       timestamp_format: str = '%Y-%m-%d %H:%M:%S',
                       turntable_mode: bool = False
                       ) -> float:
  """Calculate the time duration in secs for selected intervals.

  Calculates the time delta between given intervals in secs.

  Args:
    start_time: Starting timestamp.
    end_time: Ending timestamp.
    timestamp_format: Timestamp format (default: %Y-%m-%d %H:%M:%S) of
                      the given intervals.

  Returns:
    Timedelta in secs.
  """
  if turntable_mode:
    _start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    _end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
  else:
    _start_time = datetime.strptime(start_time, timestamp_format)
    _end_time = datetime.strptime(end_time, timestamp_format)
  return float((_end_time - _start_time).seconds)
