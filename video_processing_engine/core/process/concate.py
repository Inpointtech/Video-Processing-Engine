"""A subservice for concatenating the videos."""

import os
from pathlib import Path
from typing import List

from video_processing_engine.core.process.stats import video_file_extensions


def create_temporary_file(file: str, output: str = None) -> str:
  """Create a temporary file for FFMPEG's further processing.

  Create a temporary file for FFMPEG's PIPE based operation.

  Args:
    file: File to be converted to a temporary state.
    output: Name (default: None) of the temporary file.
  """
  if output is None:
    output = os.path.splitext(Path(file).stem)[0]
  temp_name = os.path.join(os.path.dirname(file), output)
  os.system(f'ffmpeg -loglevel error -y -i {file} -c copy -bsf:v '
            f'h264_mp4toannexb -f mpegts {temp_name}.ts')
  return f'{temp_name}.ts'


def get_concate_list(files: List) -> str:
  """Returns concatenated files list."""
  concate_string = ''
  for file in files:
    concate_string += file + '|'
  return concate_string[:-1]


def concate_videos(files: List,
                   output: str,
                   retain_stats: bool = True,
                   delete_old_files: bool = True) -> str:
  """Concatenates video.

  Concatenates videos as per the requirements.

  Args:
    file: List of files to be concatenated.
    output: Name of the output file.
    retain_stats: Boolean (default: True) to use the existing stats.
    delete_old_files: Boolean (default: True) value to delete the older
                      files once the concatenation is done.

  Returns:
    Path where the concatenated file is created.
  """
  temp_videos = []
  if len(files) == 1:
    return files[0]
  output = os.path.join(os.path.dirname(files[0]), output)
  for file in files:
    temp_file = create_temporary_file(file)
    temp_videos.append(temp_file)
  temp_string = get_concate_list(temp_videos)
  os.system(f'ffmpeg -loglevel error -y -i "concat:{temp_string}" -c copy '
            f'-bsf:a aac_adtstoasc {output}')
  if delete_old_files:
    files.extend(temp_videos)
    for file in files:
      os.remove(file)
  return output


def concate_everything_but_live(directory: str,
                                live_file: str,
                                output: str,
                                retain_stats: bool = True,
                                delete_old_files: bool = True) -> str:
  """Concatenates video except the live video.

  Concatenates all videos in the directory except the live video.

  Args:
    file: List of files to be concatenated.
    live_file: Live file to be skipped while concatenating.
    output: Path of the output file.
    retain_stats: Boolean (default: True) to use the existing stats.
    delete_old_files: Boolean (default: True) value to delete the older
                      files once the concatenation is done.

  Returns:
    Path where the concatenated file is created.
  """
  concate_files = []
  for file in os.listdir(directory):
    file = os.path.join(directory, file)
    if os.path.splitext(file)[1] in video_file_extensions:
      concate_files.append(file)
  concate_files.remove(live_file)
  return concate_videos(concate_files, output, retain_stats, delete_old_files)
