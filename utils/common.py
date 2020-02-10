"""Utility for performing common functions."""

import os
import socket
from datetime import datetime
from typing import List, Optional, Union

from video_processing_engine.vars import dev

parent_path = os.path.dirname(os.path.dirname(__file__))


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
