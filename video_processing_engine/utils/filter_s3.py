"""Utility for filtering S3 objects."""

import os
from typing import Optional, Tuple

from video_processing_engine.utils.generate import (unhash_area_code,
                                                    unhash_country_code,
                                                    unhash_timestamp)


def split_filename(file_name: str) -> Optional[Tuple]:
  """Splits the hashed S3 file name into it's respective indices."""
  file_name = os.path.basename(file_name)
  if len(file_name) == 34:
    return (unhash_country_code(file_name[:2]), file_name[2:6],
            file_name[6:8], file_name[8:10], file_name[10:15],
            unhash_area_code(file_name[15:16]), file_name[16:18],
            unhash_timestamp(file_name[18:28]), file_name[28:30])
  else:
    return None


def split_bucket_name(file_name: str) -> Optional[Tuple]:
  """Splits the hashed bucket name into it's respective indices."""
  file_name = os.path.basename(file_name)
  if len(file_name) == 10:
    return (unhash_country_code(file_name[:2]), file_name[2:6], file_name[6:8],
            file_name[8:10])
  else:
    return None
