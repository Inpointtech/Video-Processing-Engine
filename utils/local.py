"""Utility for simplifying file operations."""

import os
from typing import Optional


def get_filename(path: str) -> str:
    """Return filename."""
    name = (os.path.basename(path).split('.')[0]).lower()
    if len(name) > 10:
        return name[:11]
    else:
        return name


def get_directory_name(path: str) -> str:
  """Get directory where the videos will be stored."""
  return os.path.join(os.path.dirname(path), get_filename(path))


def create_directory(path: str) -> None:
    """Create directory with file name"""
    if not os.path.isdir(get_directory_name(path)):
      os.mkdir(get_directory_name(path))


def filename(path: str,
             video_number: int,
             extension: Optional[str] = 'mp4') -> str:
  create_directory(path)
  return os.path.join(get_directory_name(path),
                      f'{get_filename(path)}_{video_number}.{extension}')
