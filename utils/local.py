"""Utility for simplifying file operations."""

import os
import shutil
from pathlib import Path
from typing import Optional

from video_processing_engine.utils.generate import hash_x, hash_xa


def get_file_name(path: str) -> str:
  """Return filename."""
  return Path(path).stem


def get_directory_name(path: str) -> str:
  """Return directory where the video(s) will be stored."""
  return os.path.join(os.path.dirname(path), get_file_name(path))


def create_directory(path: str) -> str:
  """Create directory with filename and return its path.

  Args:
    path: Path where the directory needs to be created.

  Returns:
    String directory path.
  """
  if not os.path.isdir(get_directory_name(path)):
    os.mkdir(get_directory_name(path))
  return get_directory_name(path)


def filename(path: str,
             video_num: int,
             extension: Optional[str] = 'mp4') -> str:
  """Creates a directory to store all files and return filename.

  Args:
    path: Path where the directory needs to be created.
    video_num: Video number to append to the trimmed videos.
    extension: Video file extension (default: mp4) to be used.

  Returns:
    Complete filename with the clip number and video extension.
  """
  create_directory(path)
  return os.path.join(get_directory_name(path),
                      f'{get_file_name(path)}{hash_x(video_num)}.{extension}')


def create_copy(path: str) -> None:
  """Creates a copy of the video file."""
  return shutil.copy(path, create_directory(path))


def rename_file(original: str, rename: str) -> str:
  """Returns renamed file path."""
  os.rename(original, original.replace(Path(original).stem, rename))
  return original.replace(Path(original).stem, rename)


def beta_filename(path: str,
                  video_num: int,
                  extension: Optional[str] = 'mp4') -> str:
  """Creates a directory to store all files and return filename.

  Args:
    path: Path where the directory needs to be created.
    video_num: Video number to append to the trimmed videos.
    extension: Video file extension (default: mp4) to be used.

  Returns:
    Complete filename with the clip number and video extension.
  """
  create_directory(path)
  return os.path.join(get_directory_name(path),
                      f'{get_file_name(path)}{hash_xa(video_num)}.{extension}')
