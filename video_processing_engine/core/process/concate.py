"""A subservice for concatenating the videos."""

import os
import random
from typing import List, Optional, Union

# TODO(xames3): Remove suppressed pyright warnings.
# pyright: reportMissingTypeStubs=false
from moviepy.editor import VideoFileClip as vfc, concatenate_videoclips as cvc

from video_processing_engine.utils.common import now


def concate_videos(files: List,
                   output: str,
                   codec: Optional[str] = 'libx264',
                   bitrate: Optional[int] = 400,
                   fps: Optional[int] = 24,
                   audio: Optional[bool] = False,
                   preset: Optional[str] = 'ultrafast',
                   threads: Optional[int] = 15,
                   delete_old_files: Optional[bool] = True) -> str:
  """Concatenates video.

  Concatenates videos as per the requirements.

  Args:
    file: List of files to be concatenated.
    output: Path of the output file.
    codec: Codec (default: libx264 -> mp4) to be used for concatenation.
    bitrate: Bitrate (default: min. 400) used for the concatenation.
    fps: FPS (default: 24) of the concatenated video.
    audio: Boolean (default: False) value to have audio in concatenated
           file.
    preset: The speed (default: ultrafast) used for applying the
            concatenation technique.
    threads: Number of threads (default: 15) to be used for
             concatenation.
    delete_old_files: Boolean (default: True) value to delete the older
                      files once the concatenation is done.

  Returns:
    Path where the concatenated file is created.
  """
  videos = []
  if len(files) == 1:
    return files[0]
  output = os.path.join(os.path.dirname(files[0]), output)
  for file in files:
    videos.append(vfc(file))
  concatenated_video = cvc(videos)
  concatenated_video.write_videofile(output, codec=codec, fps=fps, audio=audio,
                                     preset=preset, threads=threads,
                                     bitrate=f'{bitrate}k', logger=None)
  if delete_old_files:
    for file in files:
      os.remove(file)
  return output


def concate_everything_but_live(directory: str,
                                live_file: str,
                                output: str,
                                codec: Optional[str] = 'libx264',
                                bitrate: Optional[int] = 400,
                                fps: Optional[int] = 24,
                                audio: Optional[bool] = False,
                                preset: Optional[str] = 'ultrafast',
                                threads: Optional[int] = 15,
                                delete_old_files: Optional[bool] = True) -> str:
  """Concatenates video except the live video.

  Concatenates all videos in the directory except the live video.

  Args:
    file: List of files to be concatenated.
    live_file: Live file to be skipped while concatenating.
    output: Path of the output file.
    codec: Codec (default: libx264 -> mp4) to be used for concatenation.
    bitrate: Bitrate (default: min. 400) used for the concatenation.
    fps: FPS (default: 24) of the concatenated video.
    audio: Boolean (default: False) value to have audio in concatenated
           file.
    preset: The speed (default: ultrafast) used for applying the
            concatenation technique.
    threads: Number of threads (default: 15) to be used for
             concatenation.
    delete_old_files: Boolean (default: True) value to delete the older
                      files once the concatenation is done.

  Returns:
    Path where the concatenated file is created.
  """
  concate_files = []
  for file in os.listdir(directory):
    file = os.path.join(directory, file)
    concate_files.append(file)
  concate_files.remove(live_file)
  return concate_videos(concate_files, output, codec, bitrate, fps, audio,
                       preset, threads, delete_old_files)
