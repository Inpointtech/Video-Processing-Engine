"""Utility for simplifying file operations."""

import os
import shutil
from pathlib import Path
from typing import Optional

# TODO(xames3): Remove suppressed pyright warnings.
# pyright: reportMissingTypeStubs=false
from video_processing_engine.utils.generate import hash_aa


def create_dir_with_same_filename(file: str) -> str:
  """Create directory with same filename and return its path.

  Args:
    file: File to be used for creating directory.

  Returns:
    Directory path.
  """
  directory_path = os.path.join(os.path.dirname(file), Path(file).stem)
  if not os.path.isdir(directory_path):
    os.mkdir(directory_path)
  return directory_path


def create_copy(file: str,
                copy_path: Optional[str] = None,
                copy_name: Optional[str] = None) -> str:
  """Create copy of the file and return path of the copied file.

  Args:
    file: File to be copied.
    copy_path: Path (default: None) where the copy needs to be created.
    copy_name: Name (default: None) of the copy file.

  Returns:
    Path where the copy is created.
  """
  if copy_path is None:
    copy_path = create_dir_with_same_filename(file)
  if copy_name is None:
    copy_name = os.path.basename(file)
  return shutil.copy(file, os.path.join(copy_path, copy_name))


def rename_original_file(file: str, bucket_name: str, order_name: str) -> str:
  """Renames original file."""
  new_name = file.replace(Path(file).stem, f'{bucket_name}{order_name}aaaa')
  os.rename(file, file.replace(Path(file).stem,
                               f'{bucket_name}{order_name}aaaa'))
  return new_name


def rename_aaaa_file(file: str, video_type: str) -> str:
  """Replaces 'aaaa' in the filename with video type sequence."""
  temp_name = ''.join([Path(file).stem[:-4], video_type])
  new_name = file.replace(Path(file).stem, temp_name)
  os.rename(file, new_name)
  return new_name


def temporary_rename(file: str, rename: Optional[str] = 'temp_xa') -> str:
  """Renames file temporarily for operation."""
  temp = os.path.splitext(file)
  return ''.join([temp[0], rename, temp[1]])


def temporary_copy(file: str) -> str:
  """Creates a temporary copy for operation."""
  temp_file = temporary_rename(file)
  return shutil.copy(file, temp_file)


def filename(file: str, video_num: int) -> str:
  """Returns filename with hashed index."""
  temp_name = os.path.splitext(file)
  return ''.join([temp_name[0], hash_aa(video_num), temp_name[1]])