"""A subservice for concatenating the videos."""

import os
from typing import Optional

from video_processing_engine.core.process.stats import duration as drn
from video_processing_engine.utils.common import file_size
from video_processing_engine.utils.common import timestamp_dirname as td


def concate_videos(directory: str,
                   delete_old_files: bool = True) -> Optional[str]:
  """Concatenates video.

  Concatenates videos as per the requirements.

  Args:
    file: List of files to be concatenated.
    output: Name of the output file.
    delete_old_files: Boolean (default: True) value to delete the older
                      files once the concatenation is done.

  Returns:
    Path where the concatenated file is created.
  """
  files = [os.path.join(directory, file) for file in os.listdir(directory)
           if file_size(os.path.join(directory, file)) != '300.0 bytes']
  files.sort(key=os.path.getctime)
  files = [f"file '{file}'\n" for file in files
           if not file.endswith('__init__.py')]
  if len(os.listdir(directory)) == 0:
    return None
  if len(os.listdir(directory)) == 1:
    if drn(os.path.join(directory, os.listdir(directory)[0])) == '300.0 bytes':
      os.remove(os.path.join(directory, os.listdir(directory)[0]))
      return None
    return os.path.join(directory, os.listdir(directory)[0])
  with open(os.path.join(directory, f'{td()}.tmp_xa'), 'w') as file:
    file.writelines(files)
  output = os.path.join(directory, f'{td()}.mp4')
  os.system(f'ffmpeg -loglevel error -y -f concat -safe 0 -i '
            f'{os.path.join(directory, f"{td()}.tmp_xa")} -vcodec copy '
            f'-acodec copy {output}')
  if delete_old_files:
    temp = [os.path.join(directory, file) for file in os.listdir(directory)
            if not os.path.join(directory, file).endswith('__init__.py')]
    try:
      temp.remove(output)
    except ValueError:
      pass
    for file in temp:
      os.remove(file)
  return output
