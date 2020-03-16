"""A subservice for compressing the videos."""

import os
from typing import Optional

from video_processing_engine.core.process.stats import bitrate as b
from video_processing_engine.utils.local import quick_rename


def calculate_cbr(file: str, ratio: int) -> str:
  """Calculates the required bitrate for compression."""
  return str(int(b(file) * (100 - ratio)))


def compress_video(file: str, ratio: int) -> Optional[str]:
  """Compresses video.

  Compresses video as per the requirements.

  Args:
    file: File to be compressed.
    ratio: Compression ratio to be applied.

  Returns:
    Path of the temporary duplicate file created.
  """
  if ratio <= 90:
    bitrate = calculate_cbr(file, ratio)
  else:
    return None
  file, temp = quick_rename(file)
  os.system(f'ffmpeg -loglevel error -y -i {temp} -vcodec copy -acodec '
            f'copy -b {bitrate} {file}')
  return temp
